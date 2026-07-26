"""The interviewer agent — a persona bound to a specific interview mode."""

from __future__ import annotations

from livekit.agents import Agent

from viva.interview.modes import InterviewMode


class Interviewer(Agent):
    """A LiveKit `Agent` whose instructions come from the chosen interview mode.

    The mode is kept on the instance so later stages (scoring, mode switches)
    can see which round was run.
    """

    def __init__(self, mode: InterviewMode) -> None:
        self.mode = mode
        super().__init__(instructions=mode.instructions())
