"""The LiveKit worker entrypoint: one job == one interview session."""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import JobContext

from viva.agent.interviewer import Interviewer
from viva.agent.session import build_session
from viva.config import get_settings
from viva.interview.modes import InterviewMode, mode_from_room_name
from viva.scoring.generate import generate_scorecard
from viva.scoring.recorder import TranscriptRecorder
from viva.storage import mark_failed, save_scorecard

logger = logging.getLogger("viva.agent")


async def entrypoint(ctx: JobContext) -> None:
    """Connect to the room, start the interviewer, and open with a greeting."""
    settings = get_settings()

    await ctx.connect()

    # The token server encodes the mode in the room name (viva-<mode>-<id>);
    # the console mock room has no such prefix and falls back to HR.
    mode = mode_from_room_name(ctx.room.name)
    logger.info("starting interview room=%s mode=%s", ctx.room.name, mode.key.value)

    session = build_session(settings)

    # Record the conversation as it happens, then score it once the call ends.
    recorder = TranscriptRecorder()
    recorder.attach(session)
    ctx.add_shutdown_callback(lambda: _score_interview(recorder, mode, ctx.room.name))

    await session.start(Interviewer(mode), room=ctx.room)

    # Let the interviewer speak first — the "incoming call" opening line.
    await session.generate_reply(instructions=mode.opening)


async def _score_interview(
    recorder: TranscriptRecorder, mode: InterviewMode, room: str
) -> None:
    """Build the scorecard after the call and store it for the client to fetch.

    Runs during job shutdown, so it must never raise — a failed scorecard should
    not take the worker down with it."""
    transcript = recorder.transcript
    if not transcript.candidate_turns():
        logger.info("no candidate speech captured, skipping scorecard")
        await asyncio.to_thread(mark_failed, room)
        return

    try:
        # Blocking SDK / DB calls — keep them off the event loop.
        scorecard = await asyncio.to_thread(generate_scorecard, transcript, mode)
        await asyncio.to_thread(save_scorecard, room, scorecard)
    except Exception:
        logger.exception("scorecard generation failed")
        await asyncio.to_thread(mark_failed, room)
        return

    logger.info(
        "scorecard ready room=%s score=%.1f/10 fillers=%d wpm=%.0f",
        room,
        scorecard.assessment.overall_score,
        scorecard.metrics.filler_word_count,
        scorecard.metrics.words_per_minute,
    )
