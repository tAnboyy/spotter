import asyncio
import json
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import google_auth_configured, verify_google_id_token
from .models import (
    AuthResult,
    CreateResult,
    CreateSession,
    Event,
    EventResult,
    GoogleAuthRequest,
    PlanPreview,
    PlanRequest,
    PongFrame,
    ProfileUpdate,
    ScheduleUpdate,
    Snapshot,
    SnapshotFrame,
    StreamAuthorization,
    UserProfile,
)
from .engine import TransitionError, preview_plan
from .store import Store, StoreError
from .voice import VoiceAuthorization, VoiceRequest, authorize_voice, voice_configured

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
CATALOG = json.loads((ROOT / "catalog/demo.json").read_text(encoding="utf-8"))
security = HTTPBearer(auto_error=False)


def bearer(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Access token required")
    return credentials.credentials


def create_app(database: str | None = None, *, voice_transport: httpx.AsyncBaseTransport | None = None, google_transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    store = Store(database or os.environ.get("DATABASE_URL") or os.environ.get("SPOTTER_DATABASE", str(ROOT / "data/spotter.sqlite3")), CATALOG)

    async def tick():
        while True:
            await asyncio.to_thread(store.expire_due)
            await asyncio.sleep(0.5)

    @asynccontextmanager
    async def lifespan(app):
        # PostgreSQL expires persisted deadlines on snapshot/event access. Active
        # streams already fetch snapshots; no idle polling keeps Neon awake.
        worker = None if store.database.postgres else asyncio.create_task(tick())
        try:
            yield
        finally:
            if worker is not None:
                worker.cancel()
                with suppress(asyncio.CancelledError):
                    await worker

    app = FastAPI(title="Spotter workout API", version="1.0.0", lifespan=lifespan)
    app.state.store = store
    app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("SPOTTER_CORS_ORIGINS", "http://localhost:8081,http://127.0.0.1:8081").split(","), allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(StoreError)
    async def store_error(_, exc: StoreError):
        return JSONResponse(status_code=exc.status, content={"message": exc.message, "snapshot": exc.snapshot})

    @app.get("/health")
    def health():
        return {"status": "ok", "schema_version": 1, "voice_configured": voice_configured(), "google_auth_configured": google_auth_configured()}

    @app.get("/catalog")
    def catalog():
        return CATALOG

    @app.post("/auth/google", response_model=AuthResult)
    async def google_sign_in(request: GoogleAuthRequest):
        identity = await verify_google_id_token(request, google_transport)
        return store.sign_in_google(identity)

    @app.get("/profile", response_model=UserProfile)
    def get_profile(token: str = Depends(bearer)):
        return store.get_profile(token)

    @app.put("/profile", response_model=UserProfile)
    def put_profile(update: ProfileUpdate, token: str = Depends(bearer)):
        return store.save_profile(token, update)

    @app.put("/profile/schedule", response_model=UserProfile)
    def put_schedule(update: ScheduleUpdate, token: str = Depends(bearer)):
        return store.save_schedule(token, update)

    @app.post("/plans/preview", response_model=PlanPreview)
    def plan_preview(request: PlanRequest):
        try:
            return preview_plan(request, CATALOG)
        except TransitionError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/sessions", status_code=201, response_model=CreateResult)
    def create(request: CreateSession):
        return store.create(request)

    @app.get("/sessions/{session_id}", response_model=Snapshot)
    def get(session_id: str, token: str = Depends(bearer)):
        return store.get(session_id, token)

    @app.post("/sessions/{session_id}/events", response_model=EventResult)
    def post_event(session_id: str, event: Event, token: str = Depends(bearer)):
        return store.event(session_id, token, event)

    @app.get("/sessions/{session_id}/summary")
    def get_summary(session_id: str, token: str = Depends(bearer)):
        return store.summary(session_id, token)

    @app.websocket("/sessions/{session_id}/stream")
    async def stream(websocket: WebSocket, session_id: str):
        await websocket.accept()
        try:
            auth = StreamAuthorization.model_validate(
                await asyncio.wait_for(websocket.receive_json(), timeout=5)
            )
            version = 0
            while True:
                state = await asyncio.to_thread(store.get, session_id, auth.access_token)
                if state["version"] > version:
                    frame = SnapshotFrame(snapshot=Snapshot.model_validate(state))
                    await websocket.send_json(frame.model_dump(mode="json"))
                    version = state["version"]
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                    if message == "ping":
                        await websocket.send_json(PongFrame().model_dump(mode="json"))
                except asyncio.TimeoutError:
                    pass
        except (WebSocketDisconnect, RuntimeError):
            return
        except (StoreError, asyncio.TimeoutError, ValueError):
            with suppress(RuntimeError):
                await websocket.close(code=1008)

    @app.post("/voice/token", response_model=VoiceAuthorization)
    async def voice_token(request: VoiceRequest, response: Response, token: str = Depends(bearer)):
        state = await asyncio.to_thread(store.get, request.session_id, token)
        if state["phase"] in {"ended", "completed"}:
            raise HTTPException(409, "Workout finished. Start a new workout before connecting voice.")
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return await authorize_voice(voice_transport)

    return app


app = create_app()
