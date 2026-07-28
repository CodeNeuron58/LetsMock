"""Async post-call scoring: turn the transcript into a Pydantic scorecard.

Deterministic delivery metrics are computed in code; the qualitative judgement
comes from the LLM as schema-validated JSON.
"""

from viva.scoring.generate import generate_scorecard
from viva.scoring.metrics import compute_metrics
from viva.scoring.schema import AnswerEvaluation, Assessment, Scorecard, SpeechMetrics
from viva.scoring.transcript import Transcript, Turn

__all__ = [
    "AnswerEvaluation",
    "Assessment",
    "Scorecard",
    "SpeechMetrics",
    "Transcript",
    "Turn",
    "compute_metrics",
    "generate_scorecard",
]
