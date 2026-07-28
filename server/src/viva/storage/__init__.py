"""Persistence for interviews and their scorecards."""

from viva.storage.models import Interview, InterviewStatus
from viva.storage.store import create_interview, get_interview, mark_failed, save_scorecard

__all__ = [
    "Interview",
    "InterviewStatus",
    "create_interview",
    "get_interview",
    "mark_failed",
    "save_scorecard",
]
