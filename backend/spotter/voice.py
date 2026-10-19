"""ElevenLabs authorization only. Workout actions remain client tools + events."""
import os

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class VoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=100)


class VoiceAuthorization(BaseModel):
    conversation_token: str = Field(min_length=1)


class ProviderToken(BaseModel):
    token: str = Field(min_length=1, strict=True)


def voice_configured() -> bool:
    return all(os.environ.get(name, "").strip() for name in ("ELEVENLABS_API_KEY", "ELEVENLABS_AGENT_ID"))


async def authorize_voice(transport: httpx.AsyncBaseTransport | None = None) -> VoiceAuthorization:
    if not voice_configured():
        raise HTTPException(503, "Voice is not configured. Set backend ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID.")
    try:
        # Shorter than the app's 12-second request deadline; never cache tokens.
        async with httpx.AsyncClient(timeout=10, transport=transport, follow_redirects=False) as client:
            result = await client.get(
                "https://api.elevenlabs.io/v1/convai/conversation/token",
                params={"agent_id": os.environ["ELEVENLABS_AGENT_ID"].strip()},
                headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"].strip()},
            )
            result.raise_for_status()
            token = ProviderToken.model_validate(result.json()).token
            if not token.strip():
                raise ValueError("Empty provider token")
            return VoiceAuthorization(conversation_token=token)
    except (httpx.HTTPError, ValidationError, ValueError) as exc:
        # Provider bodies and exception messages may contain credentials; do not expose them.
        raise HTTPException(502, "Unable to authorize the voice session. Check agent configuration and provider connectivity; workout buttons still work.") from exc
