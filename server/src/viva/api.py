"""FastAPI app that mints LiveKit access tokens so a client can join an interview.

Client flow:
  1. POST /session {"mode": "hr"}   -> {url, token, room, mode}
  2. Client connects to `url` with `token`, joining `room`.
  3. The agent worker (`agent.py dev`) is dispatched into that room and interviews.

The mode is encoded in the room name (viva-<mode>-<id>); the agent reads it back
via `mode_from_room_name`, so no separate metadata channel is needed yet.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from livekit import api
from pydantic import BaseModel

from viva.config import get_settings
from viva.interview.modes import get_mode, room_name_for

app = FastAPI(title="Viva API")


class SessionRequest(BaseModel):
    mode: str = "hr"
    identity: str | None = None


class SessionResponse(BaseModel):
    url: str
    token: str
    room: str
    mode: str


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/session", response_model=SessionResponse)
def create_session(req: SessionRequest) -> SessionResponse:
    """Mint a join token for a fresh interview room in the requested mode."""
    settings = get_settings()
    if not (settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret):
        raise HTTPException(
            status_code=503,
            detail="LiveKit credentials not set (LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET).",
        )

    mode = get_mode(req.mode)  # validates + falls back to HR
    identity = req.identity or f"candidate-{uuid.uuid4().hex[:8]}"
    room = room_name_for(mode.key)

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .to_jwt()
    )
    return SessionResponse(url=settings.livekit_url, token=token, room=room, mode=mode.key.value)
