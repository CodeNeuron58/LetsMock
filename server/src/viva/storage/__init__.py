"""Persistence for interviews and their scorecards."""

from viva.storage.models import Interview, InterviewStatus, Resume
from viva.storage.store import (
    create_interview,
    get_interview,
    get_interview_resume,
    get_resume,
    mark_failed,
    save_resume,
    save_scorecard,
)

__all__ = [
    "Interview",
    "InterviewStatus",
    "Resume",
    "create_interview",
    "get_interview",
    "get_interview_resume",
    "get_resume",
    "mark_failed",
    "save_resume",
    "save_scorecard",
]
