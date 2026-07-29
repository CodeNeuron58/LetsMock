"""Reading and writing interviews. The only place that touches the ORM."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from viva.scoring.schema import Scorecard
from viva.storage.models import Interview, InterviewStatus, new_session


def create_interview(room: str, mode: str, user_id: str | None = None) -> None:
    """Record a room as soon as its token is issued, so a client polling for a
    scorecard can tell 'not finished yet' apart from 'no such interview'."""
    with new_session() as db:
        db.add(
            Interview(
                room=room, mode=mode, user_id=user_id, status=InterviewStatus.pending
            )
        )
        db.commit()


def count_interviews(user_id: str) -> int:
    with new_session() as db:
        return db.scalar(
            select(func.count()).select_from(Interview).where(Interview.user_id == user_id)
        ) or 0


def last_interview_at(user_id: str) -> datetime | None:
    """When this user last *started* an interview (started, not finished —
    otherwise an abandoned call would be a free retry)."""
    with new_session() as db:
        return db.scalar(
            select(func.max(Interview.created_at)).where(Interview.user_id == user_id)
        )


def save_scorecard(room: str, scorecard: Scorecard) -> None:
    """Attach a finished scorecard to its interview.

    Creates the row if it is missing: the agent can run in a room the API never
    issued a token for (console mode, or a directly dispatched job), and that
    interview still happened and is still worth keeping.
    """
    with new_session() as db:
        interview = db.get(Interview, room)
        if interview is None:
            interview = Interview(room=room, mode=scorecard.mode)
            db.add(interview)
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
