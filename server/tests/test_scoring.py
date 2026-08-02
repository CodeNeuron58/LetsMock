"""Scoring: the delivery metrics computed in code, and capturing a live call.

The LLM assessment itself is not unit-tested — it costs money and its output is
not deterministic. What is tested here is everything around it.
"""

from __future__ import annotations

from viva.scoring.metrics import compute_metrics
from viva.scoring.recorder import TranscriptRecorder
from viva.scoring.transcript import Transcript, Turn


def _transcript() -> Transcript:
    return Transcript(
        turns=[
            Turn(role="interviewer", text="Tell me about yourself."),
            Turn(
                role="candidate",
                start=10,
                end=22,
                text="Um, I am a final year student and I, you know, build AI systems.",
            ),
            Turn(role="interviewer", text="What was the hardest problem you solved?"),
            Turn(
                role="candidate",
                start=30,
                end=50,
                text="I built a real time voice pipeline and latency was the hard part.",
            ),
        ]
    )


def test_pace_uses_speaking_time_not_wall_clock():
    """A nervous pause must not be counted as slow speech."""
    metrics = compute_metrics(_transcript())

    assert metrics.speaking_seconds == 32.0  # 12s + 20s, not the 40s span
    assert metrics.words_per_minute > 0


def test_filler_words_are_counted_and_broken_down():
    metrics = compute_metrics(_transcript())

    assert metrics.filler_word_count >= 2
    assert metrics.filler_breakdown["um"] == 1
    assert metrics.filler_breakdown["you know"] == 1


def test_like_is_only_a_filler_when_it_is_set_off_by_a_pause():
    """"tools like LangGraph" is a comparison; ", like," is a verbal tic. An
    inflated filler count is worse than a missed one — the candidate can count
    their own 'like's and will stop trusting the scorecard."""
    transcript = Transcript(
        turns=[
            Turn(
                role="candidate",
                start=0,
                end=10,
                text="I used tools like LangGraph and, like, Whisper for this.",
            )
        ]
    )

    assert compute_metrics(transcript).filler_breakdown.get("like") == 1


def test_pace_sums_every_burst_of_an_answer():
    """Real answers arrive in bursts with pauses between them. Counting only
    the last burst inflates words-per-minute to impossible values."""
    transcript = Transcript(
        turns=[
            Turn(role="candidate", start=0, end=60, speech_seconds=40.0, text=" ".join(["word"] * 80))
        ]
    )

    metrics = compute_metrics(transcript)

    assert metrics.speaking_seconds == 40.0  # not the 60s span
    assert metrics.words_per_minute == 120.0  # a humanly possible pace


def test_multiword_fillers_are_not_double_counted():
    """'you know' must not also register as a bare 'know'-style single hit."""
    transcript = Transcript(
        turns=[Turn(role="candidate", start=0, end=10, text="you know, you know, um")]
    )

    metrics = compute_metrics(transcript)

    assert metrics.filler_breakdown["you know"] == 2
    assert metrics.filler_word_count == 3  # 2 + one "um"


def test_interviewer_speech_is_excluded_from_the_candidate_metrics():
    transcript = Transcript(
        turns=[
            Turn(role="interviewer", text="um um um um um um um um"),
            Turn(role="candidate", start=0, end=10, text="A clear answer."),
        ]
    )

    assert compute_metrics(transcript).filler_word_count == 0


def test_metrics_survive_a_transcript_with_no_timings():
    transcript = Transcript(turns=[Turn(role="candidate", text="No timestamps here.")])

    metrics = compute_metrics(transcript)

    assert metrics.words_per_minute == 0.0  # unknown, not a divide-by-zero
    assert metrics.candidate_word_count == 3


# --- capturing a live session -------------------------------------------------


def _msg(role: str, text: str):
    from livekit.agents import ConversationItemAddedEvent
    from livekit.agents.llm import ChatMessage

    return ConversationItemAddedEvent(item=ChatMessage(role=role, content=[text]))


def _state(old: str, new: str, at: float):
    from livekit.agents import UserStateChangedEvent

    return UserStateChangedEvent(old_state=old, new_state=new, created_at=at)


def test_recorder_matches_speaking_windows_to_the_right_turns():
    recorder = TranscriptRecorder()

    recorder._on_item(_msg("assistant", "Tell me about yourself."))
    recorder._on_user_state(_state("listening", "speaking", 10.0))
    recorder._on_user_state(_state("speaking", "listening", 22.0))
    recorder._on_item(_msg("user", "I build AI systems."))

    turns = recorder.transcript.turns
    assert [t.role for t in turns] == ["interviewer", "candidate"]
    assert turns[1].duration == 12.0
    assert turns[0].start is None  # the interviewer's speech is not timed


def test_recorder_ignores_empty_items():
    recorder = TranscriptRecorder()

    recorder._on_item(_msg("assistant", "   "))

    assert recorder.transcript.turns == []


def test_recorder_accumulates_speech_across_bursts_of_one_answer():
    """The bug this guards: a candidate trails off and continues several times
    before the turn commits. Keeping only the final burst made pace read ~280
    words per minute — impossible, and instantly untrustworthy."""
    recorder = TranscriptRecorder()

    recorder._on_item(_msg("assistant", "Tell me about a project."))
    for start, end in [(10.0, 20.0), (24.0, 34.0), (40.0, 42.0)]:  # 22s of speech
        recorder._on_user_state(_state("listening", "speaking", start))
        recorder._on_user_state(_state("speaking", "listening", end))
    recorder._on_item(_msg("user", "A long answer said in three goes."))

    turn = recorder.transcript.candidate_turns()[0]
    assert turn.speaking_time == 22.0  # not just the final 2s burst
    assert turn.duration == 32.0  # the span, pauses included, is still recorded


def test_a_speaking_window_is_not_reused_by_a_later_turn():
    recorder = TranscriptRecorder()

    recorder._on_user_state(_state("listening", "speaking", 0.0))
    recorder._on_user_state(_state("speaking", "listening", 5.0))
    recorder._on_item(_msg("user", "First answer."))
    recorder._on_item(_msg("user", "Continuation with no new window."))

    turns = recorder.transcript.candidate_turns()
    assert turns[0].duration == 5.0
    assert turns[1].duration is None
