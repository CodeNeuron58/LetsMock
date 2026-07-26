"""Async post-call scoring: turn the transcript into a Pydantic scorecard.

Stub for now — the schema is defined so the shape is fixed; wiring the LLM pass
that fills it is a later milestone.
"""

from viva.scoring.schema import AnswerEvaluation, Scorecard

__all__ = ["AnswerEvaluation", "Scorecard"]
