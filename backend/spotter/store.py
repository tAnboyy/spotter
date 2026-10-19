import hashlib
import json
import secrets
from contextlib import AbstractContextManager
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .database import Connection, Database
from .engine import TransitionError, expire_rest, new_session, summary, transition, utc_now
from .models import CreateSession, Event, Preferences, ProfileUpdate, ScheduleUpdate


class StoreError(Exception):
    def __init__(self, message: str, status: int, snapshot: dict | None = None):
        self.message, self.status, self.snapshot = message, status, snapshot


class Store:
    def __init__(self, path: str, catalog: dict):
        self.path, self.catalog = path, catalog
        self.database = Database(path)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            if not db.execute("SELECT version FROM schema_migrations WHERE version=?", (1,)).fetchone():
                migration = Path(__file__).with_name("migrations") / "001_initial.sql"
                db.executescript(migration.read_text(encoding="utf-8"))
                db.execute("INSERT INTO schema_migrations VALUES (?)", (1,))

    def connect(self) -> AbstractContextManager[Connection]:
        return self.database.connect()

    def create(self, request: CreateSession) -> dict:
        try:
            state = new_session(request, self.catalog, utc_now())
        except TransitionError as exc:
            raise StoreError(str(exc), 422) from exc
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("INSERT INTO sessions VALUES (?,?,?)", (state["session_id"], self.digest(token), json.dumps(state)))
        return {"snapshot": state, "access_token": token}

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def load(self, db: Connection, session_id: str, token: str) -> dict:
        row = db.execute("SELECT token_hash,state FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row or not secrets.compare_digest(row[0], self.digest(token)):
            raise StoreError("Session not found or token invalid", 401)
        state = json.loads(row[1])
        if self.hydrate_state(state):
            self.save(db, state)
        return state

    @staticmethod
    def save(db: Connection, state: dict) -> None:
        db.execute("UPDATE sessions SET state=? WHERE id=?", (json.dumps(state), state["session_id"]))

    def hydrate_exercise(self, exercise: dict) -> bool:
        catalog_exercise = next((item for item in self.catalog["exercises"] if item["id"] == exercise.get("id")), None)
        defaults = {
            "primary_muscle_group": "unknown",
            "secondary_muscle_groups": [],
            "weight_min_lb": 5,
            "weight_max_lb": 500,
            "weight_step_lb": 5,
            "troubleshooting": "Ask gym staff to verify this machine's setup.",
            "stop_conditions": "Stop for sharp pain, dizziness, numbness, or abnormal machine movement.",
            "sources": [{"title": "Legacy session guidance", "url": "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/weight-training/art-20045842"}],
            "review_status": "professional_review_pending",
        }
        changed = False
        for key, fallback in defaults.items():
            if key not in exercise:
                exercise[key] = deepcopy(catalog_exercise[key]) if catalog_exercise and key in catalog_exercise else deepcopy(fallback)
                changed = True
        if "instance_id" in exercise and "weight_lb" not in exercise:
            exercise["weight_lb"] = None
            changed = True
        if "instance_id" in exercise and "set_records" not in exercise:
            exercise["set_records"] = []
            changed = True
        return changed

    def hydrate_state(self, state: dict) -> bool:
        changed = False
        if "set_started_at" not in state:
            state["set_started_at"] = None
            changed = True
        entries = state["queue"] + state["deferred"] + state["completed"] + state["skipped"]
        if state["current"]:
            entries.append(state["current"])
        if state["pending_alternative"]:
            entries.append(state["pending_alternative"])
        for exercise in entries:
            changed = self.hydrate_exercise(exercise) or changed
        return changed

    def get(self, session_id: str, token: str, now: datetime | None = None) -> dict:
        now = now or utc_now()
        with self.connect() as db:
            state = self.load(db, session_id, token)
            if expire_rest(state, now):
                self.save(db, state)
            state["server_time"] = now.isoformat()
            return state

    def event(self, session_id: str, token: str, event: Event, now: datetime | None = None) -> dict:
        now = now or utc_now()
        request = event.model_dump_json()
        with self.connect() as db:
            state = self.load(db, session_id, token)
            previous = db.execute("SELECT request,result FROM events WHERE session_id=? AND event_id=?", (session_id, str(event.event_id))).fetchone()
            if previous:
                if previous[0] != request:
                    raise StoreError("Event ID was already used with different content", 409, state)
                replayed = json.loads(previous[1])
                self.hydrate_state(replayed)
                return {"snapshot": replayed, "replayed": True}
            if expire_rest(state, now):
                self.save(db, state)
            if state["version"] != event.expected_version:
                # Commit the server timer transition even when rejecting stale input.
                db.commit()
                raise StoreError("Session changed. Refresh and choose your action again.", 409, state)
            try:
                state = transition(state, event, self.catalog, now)
            except TransitionError as exc:
                raise StoreError(str(exc), 422, state) from exc
            self.save(db, state)
            db.execute("INSERT INTO events VALUES (?,?,?,?)", (session_id, str(event.event_id), request, json.dumps(state)))
            return {"snapshot": state, "replayed": False}

    def summary(self, session_id: str, token: str) -> dict:
        return summary(self.get(session_id, token))

    def profile_from_row(self, row: tuple) -> dict:
        return {
            "user_id": row[0],
            "email": row[1] or None,
            "name": row[2],
            "preferences": json.loads(row[3]),
            "muscle_group_ids": json.loads(row[4]),
            "plan": json.loads(row[5]) if row[5] else None,
            "schedule": json.loads(row[6]) if len(row) > 6 else [],
        }

    def load_profile(self, db: Connection, token: str) -> tuple:
        row = db.execute(
            "SELECT u.id,u.email,u.name,u.preferences,u.muscle_group_ids,u.plan,COALESCE(s.schedule,'[]') FROM users u LEFT JOIN user_schedules s ON s.user_id=u.id WHERE u.token_hash=?",
            (self.digest(token),),
        ).fetchone()
        if not row:
            raise StoreError("Profile not found or token invalid", 401)
        return row

    def sign_in_google(self, identity: dict[str, str]) -> dict:
        token = secrets.token_urlsafe(32)
        defaults = Preferences().model_dump(mode="json")
        with self.connect() as db:
            existing = db.execute(
                "SELECT u.id,u.email,u.name,u.preferences,u.muscle_group_ids,u.plan,COALESCE(s.schedule,'[]') FROM users u LEFT JOIN user_schedules s ON s.user_id=u.id WHERE u.google_sub=?",
                (identity["google_sub"],),
            ).fetchone()
            if existing:
                db.execute("UPDATE users SET token_hash=?, email=? WHERE google_sub=?", (self.digest(token), identity["email"] or None, identity["google_sub"]))
                profile = self.profile_from_row(existing)
                profile["email"] = identity["email"] or None
            else:
                user_id = str(uuid4())
                db.execute(
                    "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                    (user_id, identity["google_sub"], identity["email"] or None, identity["name"], self.digest(token), json.dumps(defaults), "[]", None),
                )
                profile = {
                    "user_id": user_id,
                    "email": identity["email"] or None,
                    "name": identity["name"],
                    "preferences": defaults,
                    "muscle_group_ids": [],
                    "plan": None,
                    "schedule": [],
                }
        return {"profile": profile, "access_token": token}

    def get_profile(self, token: str) -> dict:
        with self.connect() as db:
            row = self.load_profile(db, token)
        return self.profile_from_row(row)

    def save_profile(self, token: str, update: ProfileUpdate) -> dict:
        with self.connect() as db:
            row = self.load_profile(db, token)
            db.execute(
                "UPDATE users SET name=?, preferences=?, muscle_group_ids=?, plan=? WHERE id=?",
                (
                    update.name,
                    update.preferences.model_dump_json(),
                    json.dumps(update.muscle_group_ids),
                    json.dumps([item.model_dump(mode="json") for item in update.plan]) if update.plan is not None else None,
                    row[0],
                ),
            )
        return {
            "user_id": row[0],
            "email": row[1] or None,
            "name": update.name,
            "preferences": update.preferences.model_dump(mode="json"),
            "muscle_group_ids": update.muscle_group_ids,
            "plan": [item.model_dump(mode="json") for item in update.plan] if update.plan is not None else None,
            "schedule": json.loads(row[6]),
        }

    def save_schedule(self, token: str, update: ScheduleUpdate) -> dict:
        with self.connect() as db:
            row = self.load_profile(db, token)
            preferences = Preferences.model_validate_json(row[3])
            for workout in update.schedule:
                try:
                    new_session(CreateSession(preferences=preferences, selected_muscle_group_ids=workout.muscle_group_ids, plan=workout.plan), self.catalog, utc_now())
                except TransitionError as exc:
                    raise StoreError(str(exc), 422) from exc
            schedule = [workout.model_dump(mode="json") for workout in sorted(update.schedule, key=lambda item: item.weekday)]
            db.execute("INSERT INTO user_schedules VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET schedule=excluded.schedule", (row[0], json.dumps(schedule)))
            profile = self.profile_from_row(row)
            profile["schedule"] = schedule
            return profile

    def expire_due(self) -> None:
        now = utc_now()
        with self.connect() as db:
            for row in db.execute("SELECT state FROM sessions").fetchall():
                state = json.loads(row[0])
                if expire_rest(state, now):
                    self.save(db, state)
