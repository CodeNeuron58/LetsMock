"""Capture a live interview into a `Transcript` the scorecard can be built from.

Two event streams are combined:

* ``conversation_item_added`` gives the finalised text of each turn (candidate
  and interviewer), but only tells us *when the text arrived*.
* ``user_state_changed`` brackets when the candidate was actually **speaking**
  (``speaking`` -> ``listening``), which is what words-per-minute needs.

Each candidate turn is matched to the most recent completed speaking window, so
pace is measured against real speech time rather than wall-clock gaps.
"""

from __future__ import annotations

import logging

from livekit.agents import AgentSession, ConversationItemAddedEvent, UserStateChangedEvent
from livekit.agents.llm import ChatMessage

from viva.scoring.transcript import Transcript, Turn

logger = logging.getLogger("viva.scoring.recorder")


class TranscriptRecorder:
    """Subscribes to an `AgentSession` and accumulates the interview transcript."""

    def __init__(self) -> None:
        self._turns: list[Turn] = []
        self._speech_start: float | None = None
        self._last_speech: tuple[float, float] | None = None  # (start, end)

    def attach(self, session: AgentSession) -> None:
        session.on("user_state_changed", self._on_user_state)
        session.on("conversation_item_added", self._on_item)

    @property
    def transcript(self) -> Transcript:
        return Transcript(turns=list(self._turns))

    # --- event handlers -------------------------------------------------

    def _on_user_state(self, ev: UserStateChangedEvent) -> None:
        if ev.new_state == "speaking":
            self._speech_start = ev.created_at
        elif ev.old_state == "speaking" and self._speech_start is not None:
            self._last_speech = (self._speech_start, ev.created_at)
            self._speech_start = None

    def _on_item(self, ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if not isinstance(item, ChatMessage):
            return  # agent handoffs etc. aren't part of the interview record
        text = (item.text_content or "").strip()
        if not text:
            return

        if item.role == "user":
            # Consume the matching speaking window so it can't be reused by a
            # later turn (e.g. when one utterance arrives as two items).
            start = end = None
            if self._last_speech is not None:
                start, end = self._last_speech
                self._last_speech = None
            self._turns.append(Turn(role="candidate", text=text, start=start, end=end))
        elif item.role == "assistant":
            self._turns.append(Turn(role="interviewer", text=text))
