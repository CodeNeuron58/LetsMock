"""Interview transcript: the timestamped turns the scorecard is computed from."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Turn(BaseModel):
    role: Literal["interviewer", "candidate"]
    text: str
    start: float | None = None  # seconds from call start, if known
    end: float | None = None
    # Time actually spent speaking, summed across bursts. A candidate rarely
    # says a whole answer in one go — they trail off, think, and continue — so
    # `end - start` includes their pauses and would understate their pace.
    speech_seconds: float | None = None

    @property
    def duration(self) -> float | None:
        """How long this turn spanned, pauses included."""
        if self.start is None or self.end is None:
            return None
        return max(0.0, self.end - self.start)

    @property
    def speaking_time(self) -> float | None:
        """Time spent actually talking — what pace should be measured against."""
        return self.speech_seconds if self.speech_seconds is not None else self.duration


class Transcript(BaseModel):
    turns: list[Turn]

    def candidate_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.role == "candidate"]

    def as_text(self) -> str:
        return "\n".join(f"{t.role.upper()}: {t.text}" for t in self.turns)
