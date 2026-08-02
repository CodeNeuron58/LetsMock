"""Deterministic delivery metrics — filler words and pace — computed in code so
the numbers on the scorecard are real, not the LLM's guess.

Filler set is intentionally conservative: clear disfluencies ("um", "uh") plus
common hedges ("like", "you know"). Words too often legitimate ("so", "right")
are excluded to avoid inflating the count. Tune `_SINGLEWORD_FILLERS` as needed.
"""

from __future__ import annotations

import re

from viva.scoring.schema import SpeechMetrics
from viva.scoring.transcript import Transcript

# Multi-word fillers are matched (and stripped) before single-word ones so their
# component words aren't double-counted.
_MULTIWORD_FILLERS = ("you know", "i mean", "sort of", "kind of")
_SINGLEWORD_FILLERS = frozenset(
    {"um", "uh", "erm", "uhm", "hmm", "basically", "actually", "literally"}
)
# "like" is only filler when it is set off by a pause — "I used, like, Whisper".
# In "tools like LangGraph" it is a real comparison, and counting those makes
# the filler total look wrong to the person reading their own scorecard.
_FILLER_LIKE = re.compile(r"(?:,\s*like\b|\blike\s*,)")
_WORD = re.compile(r"[a-z']+")


def compute_metrics(transcript: Transcript) -> SpeechMetrics:
    turns = transcript.candidate_turns()
    text = " ".join(t.text for t in turns).lower()

    breakdown: dict[str, int] = {}
    working = text
    for phrase in _MULTIWORD_FILLERS:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        hits = len(re.findall(pattern, working))
        if hits:
            breakdown[phrase] = hits
            working = re.sub(pattern, " ", working)
    if hits := len(_FILLER_LIKE.findall(working)):
        breakdown["like"] = hits
        working = _FILLER_LIKE.sub(" ", working)
    for word in _WORD.findall(working):
        if word in _SINGLEWORD_FILLERS:
            breakdown[word] = breakdown.get(word, 0) + 1

    total_words = len(_WORD.findall(text))
    # Pace is measured against time actually spent talking, not the wall-clock
    # span, so thinking pauses don't read as slow speech.
    speaking = sum(s for t in turns if (s := t.speaking_time) is not None)
    wpm = round(total_words / (speaking / 60), 1) if speaking > 0 else 0.0

    return SpeechMetrics(
        candidate_word_count=total_words,
        speaking_seconds=round(speaking, 1),
        words_per_minute=wpm,
        filler_word_count=sum(breakdown.values()),
        filler_breakdown=dict(sorted(breakdown.items(), key=lambda kv: -kv[1])),
    )
