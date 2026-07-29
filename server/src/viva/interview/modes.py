"""The interview modes and the prompts that give each one its character.

One shared persona (how the interviewer *speaks* — short, spoken, one question
at a time, patient with pauses) plus a per-mode `guidance` block (what the round
is *about*) and an `opening` instruction (how to kick it off).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

# The shared voice-interviewer persona. Every mode inherits this.
BASE_PERSONA = """\
You are Viva, a sharp, professional job interviewer running a live voice interview. \
You are fair but you do not go easy — this is practice for a real, high-stakes interview.

How you speak (this is a VOICE call, your words are spoken aloud):
- Keep every reply short: one or two sentences. Never lecture or give lists.
- Ask exactly ONE question at a time, then stop and listen.
- Sound like a real person on a phone call. Use brief acknowledgements \
("Right.", "Okay, got it.") before moving on.
- Never speak headings, bullet points, or markdown — spoken words only.

How you interview:
- Build on the candidate's answer and probe deeper with follow-ups. If an answer \
is vague, push for specifics: "Can you be concrete about what *you* did?"
- Occasionally throw a harder follow-up or a curveball to see how they think under pressure.
- Do NOT give feedback, scores, or coaching during the interview. Stay in character. \
Detailed feedback comes afterwards.
- If the candidate pauses, wait — they may be thinking. Do not fill every silence.
- Keep things moving and cover a few substantial questions.

Stay in role at all times."""


class Mode(str, Enum):
    HR = "hr"
    RESUME = "resume"
    SDE = "sde"


@dataclass(frozen=True)
class InterviewMode:
    key: Mode
    display_name: str
    focus: str
    guidance: str
    opening: str

    def instructions(self) -> str:
        """Full system prompt: shared persona + this mode's guidance."""
        return f"{BASE_PERSONA}\n\n--- This round ---\n{self.guidance}"


MODES: dict[Mode, InterviewMode] = {
    Mode.HR: InterviewMode(
        key=Mode.HR,
        display_name="HR / Behavioural",
        focus="behavioural and motivational questions",
        guidance=(
            "This is an HR / behavioural round. Focus on motivation, teamwork, "
            "handling conflict, strengths and weaknesses, and 'tell me about a time "
            "when...' situations. Listen for structure (situation, action, result) and "
            "probe for specifics and genuine ownership rather than vague generalities."
        ),
        opening=(
            "Greet the candidate briefly, introduce yourself as their interviewer for "
            "an HR round, and ask them to tell you a little about themselves."
        ),
    ),
    Mode.RESUME: InterviewMode(
        key=Mode.RESUME,
        display_name="Resume Grill",
        focus="a deep dive into their projects and experience",
        guidance=(
            "This is a resume deep-dive. Grill the candidate on the specific projects "
            "and experience they describe. Drill into technical decisions and trade-offs: "
            "'Why did you choose that?', 'What broke?', 'What would you do differently?'. "
            "Catch hand-waving. (Parsed resume text will be supplied in a later version; "
            "for now, ask them to describe their most significant project, then grill it.)"
        ),
        opening=(
            "Greet the candidate briefly, introduce yourself as their interviewer, and "
            "ask them to walk you through the project they are most proud of."
        ),
    ),
    Mode.SDE: InterviewMode(
        key=Mode.SDE,
        display_name="Tech Concepts (SDE)",
        focus="computer-science fundamentals, spoken answers only",
        guidance=(
            "This is a technical-concepts round for a software role — spoken answers "
            "only, no coding. Ask about CS fundamentals: data structures, complexity, "
            "databases and indexing, concurrency, basic system design, APIs. One concept "
            "at a time. Follow up to test depth of understanding, not memorisation."
        ),
        opening=(
            "Greet the candidate briefly, introduce yourself as their technical "
            "interviewer, and start with one straightforward CS-fundamentals question."
        ),
    ),
}


def get_mode(key: str | Mode) -> InterviewMode:
    """Look up a mode by key, falling back to HR for anything unrecognised."""
    try:
        return MODES[Mode(key)]
    except (ValueError, KeyError):
        return MODES[Mode.HR]


# What the interviewer is told when the interview is nearly out of time. It is
# swapped in as the agent's instructions, so the close happens on its next turn
# instead of cutting the candidate off mid-answer.
WRAP_UP_INSTRUCTIONS = """\
The interview is almost out of time. Do NOT start any new topic.

Finish the current exchange briefly, then close the interview: thank the \
candidate by acknowledging one specific thing they talked about, tell them \
their detailed feedback is on its way, and wish them luck. Keep the whole \
closing to two or three sentences, and do not ask another question."""

DEFAULT_MINUTES = 5


@dataclass(frozen=True)
class RoomInfo:
    """What a room name tells the agent about the interview to run."""

    mode: InterviewMode
    minutes: int


def room_name_for(mode: str | Mode, minutes: int = DEFAULT_MINUTES) -> str:
    """Room name carrying both the mode and the length cap, e.g.
    'viva-hr-5-a1b2c3d4'. The agent parses it back with `parse_room_name`;
    encoding it here avoids a second channel just to pass two values."""
    m = get_mode(mode)
    return f"viva-{m.key.value}-{minutes}-{uuid.uuid4().hex[:8]}"


def parse_room_name(name: str) -> RoomInfo:
    """Recover mode and length from a room name built by `room_name_for`.
    Anything unexpected (e.g. the console mock room) falls back to defaults."""
    parts = name.split("-")
    if len(parts) >= 3 and parts[0] == "viva":
        minutes = int(parts[2]) if parts[2].isdigit() else DEFAULT_MINUTES
        return RoomInfo(mode=get_mode(parts[1]), minutes=minutes)
    return RoomInfo(mode=MODES[Mode.HR], minutes=DEFAULT_MINUTES)
