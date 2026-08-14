"""Reading and writing interviews. The only place that touches the ORM."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select

from viva.scoring.schema import Scorecard
from viva.storage.models import Interview, InterviewStatus, Resume, new_session


def create_interview(
    room: str, mode: str, user_id: str | None = None, resume_text: str | None = None
) -> None:
    """Record a room as soon as its token is issued, so a client polling for a
    scorecard can tell 'not finished yet' apart from 'no such interview'."""
    with new_session() as db:
        db.add(
            Interview(
                room=room,
                mode=mode,
                user_id=user_id,
                resume_text=resume_text,
                status=InterviewStatus.pending,
            )
        )
        db.commit()


def save_resume(user_id: str, filename: str, text: str) -> None:
    """Store (or replace) the candidate's resume."""
    with new_session() as db:
        resume = db.get(Resume, user_id)
        if resume is None:
            db.add(Resume(user_id=user_id, filename=filename, text=text))
        else:
            resume.filename = filename
            resume.text = text
            resume.uploaded_at = datetime.now(UTC)
        db.commit()


def get_resume(user_id: str | None) -> Resume | None:
    if not user_id:
        return None
    with new_session() as db:
        return db.get(Resume, user_id)


def get_interview_resume(room: str) -> str | None:
    """The resume text this interview was created with (used by the agent)."""
    with new_session() as db:
        interview = db.get(Interview, room)
        return interview.resume_text if interview else None


def count_interviews(user_id: str) -> int:
    with new_session() as db:
        return (
            db.scalar(
                select(func.count()).select_from(Interview).where(Interview.user_id == user_id)
            )
            or 0
        )


def last_interview_at(user_id: str) -> datetime | None:
    """When this user last *started* an interview (started, not finished —
    otherwise an abandoned call would be a free retry)."""
    with new_session() as db:
        return db.scalar(select(func.max(Interview.created_at)).where(Interview.user_id == user_id))


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
        interview.scored_at = datetime.now(UTC)
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
