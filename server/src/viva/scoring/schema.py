"""The scorecard — the product's payoff, produced async after the call.

Defined now so the whole system agrees on the shape; the scoring pass that
populates it from the transcript lands in a later milestone.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    """One question-and-answer, evaluated."""

    question: str
    what_you_said: str = Field(description="Short summary of the candidate's answer")
    strong_answer: str = Field(description="What a strong candidate would have said")
    score: float = Field(ge=0, le=10)
    flags: list[str] = Field(default_factory=list, description="Specific weaknesses")


class Scorecard(BaseModel):
    """The full report handed to the candidate after the interview."""

    mode: str
    overall_score: float = Field(ge=0, le=10)
    summary: str

    per_answer: list[AnswerEvaluation] = Field(default_factory=list)

    filler_word_count: int = 0
    words_per_minute: float | None = None
    red_flags: list[str] = Field(default_factory=list)

    transcript: str = ""
