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
from fastapi.responses import JSONResponse
from livekit import api
from pydantic import BaseModel

from viva.config import get_settings
from viva.interview.modes import get_mode, room_name_for
from viva.quota import check_quota
from viva.scoring.schema import Scorecard
from viva.storage import InterviewStatus, create_interview, get_interview

app = FastAPI(title="Viva API")


class SessionRequest(BaseModel):
    mode: str = "hr"
    identity: str | None = None
    # RevenueCat app user id + entitlement, used for the free-tier quota.
    # TODO(security): `is_pro` is client-asserted and therefore spoofable.
    # Verify it server-side against RevenueCat's REST API before launch.
    user_id: str | None = None
    is_pro: bool = False


class SessionResponse(BaseModel):
    url: str
    token: str
    room: str
    mode: str
    minutes: int  # length cap for this interview (free vs Pro)


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

    # The free tier is enforced here, not by RevenueCat.
    quota = check_quota(req.user_id, req.is_pro)
    if not quota.allowed:
        raise HTTPException(
            status_code=402,  # Payment Required — the client shows the paywall
            detail={
                "reason": quota.reason,
                "next_available": quota.next_available.isoformat()
                if quota.next_available
                else None,
            },
        )

    mode = get_mode(req.mode)  # validates + falls back to HR
    identity = req.identity or f"candidate-{uuid.uuid4().hex[:8]}"
    room = room_name_for(mode.key, quota.minutes)  # the agent reads the cap back off this

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .to_jwt()
    )
    create_interview(room, mode.key.value, user_id=req.user_id)
    return SessionResponse(
        url=settings.livekit_url,
        token=token,
        room=room,
        mode=mode.key.value,
        minutes=quota.minutes,
    )


class ScorecardResponse(BaseModel):
    status: InterviewStatus
    scorecard: Scorecard | None = None


@app.get("/scorecard/{room}", response_model=ScorecardResponse)
def read_scorecard(room: str) -> JSONResponse:
    """Fetch an interview's scorecard.

    Scoring runs after the call ends, so the client polls: 202 while the
    scorecard is still being produced, 200 once it is ready (or failed).
    """
    interview = get_interview(room)
    if interview is None:
        raise HTTPException(status_code=404, detail="No such interview.")

    body = ScorecardResponse(
        status=interview.status,
        scorecard=Scorecard.model_validate(interview.scorecard) if interview.scorecard else None,
    )
    code = 202 if interview.status is InterviewStatus.pending else 200
    return JSONResponse(status_code=code, content=body.model_dump(mode="json"))
