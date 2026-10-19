import os

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from .models import GoogleAuthRequest


def google_auth_configured() -> bool:
    return bool(os.environ.get("GOOGLE_CLIENT_ID", "").strip())


async def verify_google_id_token(request: GoogleAuthRequest, transport: httpx.AsyncBaseTransport | None = None) -> dict[str, str]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(503, "Google sign-in is not configured. Set backend GOOGLE_CLIENT_ID.")
    try:
        async with httpx.AsyncClient(transport=transport, timeout=10.0, follow_redirects=False) as client:
            result = await client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": request.id_token})
        if result.status_code != 200:
            raise HTTPException(401, "Google sign-in was rejected. Try again.")
        payload = result.json()
        if not isinstance(payload, dict) or payload.get("aud") != client_id or not str(payload.get("sub") or "").strip():
            raise HTTPException(401, "Google sign-in token did not match this app.")
        verified = str(payload.get("email_verified", "")).lower()
        email = str(payload.get("email") or "").strip() or None
        if email and verified not in {"true", "1"}:
            raise HTTPException(401, "Google email is not verified.")
        name = str(payload.get("name") or email or "You").strip()[:60] or "You"
        return {"google_sub": str(payload["sub"]), "email": email or "", "name": name}
    except HTTPException:
        raise
    except (httpx.HTTPError, ValidationError, ValueError, TypeError):
        raise HTTPException(502, "Google sign-in could not be verified. Try again.") from None
