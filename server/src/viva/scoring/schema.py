"""The scorecard — the product's payoff, produced async after the call.

Two clearly separated halves:
  * `Assessment`    — qualitative judgement, produced by the LLM.
  * `SpeechMetrics` — deterministic counts, computed in code (never the LLM), so
                      the filler/pace numbers are trustworthy, not hallucinated.
`Scorecard` bundles both.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    """One question-and-answer, evaluated by the LLM."""

    question: str = Field(description="The interviewer's question, quoted or paraphrased")
    what_you_said: str = Field(description="One-line summary of the candidate's answer")
    strong_answer: str = Field(description="What a strong candidate would have said instead")
    score: float = Field(ge=0, le=10, description="Score for this answer, 0-10")
    flags: list[str] = Field(default_factory=list, description="Specific weaknesses in this answer")


class Assessment(BaseModel):
    """The qualitative judgement the LLM produces (no computed metrics here)."""

    overall_score: float = Field(ge=0, le=10, description="Overall interview score, 0-10")
    summary: str = Field(description="2-3 sentences, brutally honest but fair")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(
        default_factory=list, description="Serious problems a real interviewer would flag"
    )
    structure_note: str = Field(
        description="How well answers were structured (e.g. STAR for behavioural rounds)"
    )
    per_answer: list[AnswerEvaluation] = Field(default_factory=list)


class SpeechMetrics(BaseModel):
    """Deterministic delivery metrics, computed from the timestamped transcript."""

    candidate_word_count: int = 0
    speaking_seconds: float = 0.0
    words_per_minute: float = 0.0
    filler_word_count: int = 0
    filler_breakdown: dict[str, int] = Field(default_factory=dict)


class Scorecard(BaseModel):
    """The full report handed to the candidate after the interview."""

    mode: str
    assessment: Assessment
    metrics: SpeechMetrics
    transcript: str = ""
