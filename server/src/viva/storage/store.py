"""Reading and writing interviews. The only place that touches the ORM."""

from __future__ import annotations

from datetime import datetime, timezone

from viva.scoring.schema import Scorecard
from viva.storage.models import Interview, InterviewStatus, new_session


def create_interview(room: str, mode: str) -> None:
    """Record a room as soon as its token is issued, so a client polling for a
    scorecard can tell 'not finished yet' apart from 'no such interview'."""
    with new_session() as db:
        db.add(Interview(room=room, mode=mode, status=InterviewStatus.pending))
        db.commit()


def save_scorecard(room: str, scorecard: Scorecard) -> None:
    """Attach a finished scorecard to its interview (no-op if the room is gone)."""
    with new_session() as db:
        interview = db.get(Interview, room)
        if interview is None:
            return
        interview.scorecard = scorecard.model_dump(mode="json")
        interview.status = InterviewStatus.scored
        interview.scored_at = datetime.now(timezone.utc)
        db.commit()


def mark_failed(room: str) -> None:
    """The call happened but scoring failed — distinct from still running."""
    with new_session() as db:
        interview = db.get(Interview, room)
        if interview is None:
            return
        interview.status = InterviewStatus.failed
        db.commit()


def get_interview(room: str) -> Interview | None:
    with new_session() as db:
        return db.get(Interview, room)
