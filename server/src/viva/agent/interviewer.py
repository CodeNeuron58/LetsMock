"""The interviewer agent — a persona bound to a specific interview mode."""

from __future__ import annotations

from livekit.agents import Agent

from viva.interview.modes import InterviewMode


class Interviewer(Agent):
    """A LiveKit `Agent` whose instructions come from the chosen interview mode.

    The mode is kept on the instance so later stages (scoring, mode switches)
    can see which round was run.
    """

    def __init__(self, mode: InterviewMode, resume_text: str | None = None) -> None:
        self.mode = mode
        self.resume_text = resume_text
        super().__init__(instructions=mode.instructions(resume_text))
