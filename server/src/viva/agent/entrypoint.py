"""The LiveKit worker entrypoint: one job == one interview session."""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import JobContext

from viva.agent.interviewer import Interviewer
from viva.agent.session import build_session
from viva.config import get_settings
from viva.interview.flow import run_interview_clock
from viva.interview.modes import InterviewMode, parse_room_name
from viva.scoring.generate import generate_scorecard
from viva.scoring.recorder import TranscriptRecorder
from viva.storage import get_interview_resume, mark_failed, save_scorecard

logger = logging.getLogger("viva.agent")


async def entrypoint(ctx: JobContext) -> None:
    """Connect to the room, start the interviewer, and open with a greeting."""
    settings = get_settings()

    await ctx.connect()

    # The token server encodes the mode and length cap in the room name
    # (viva-<mode>-<minutes>-<id>); the console mock room falls back to defaults.
    room = parse_room_name(ctx.room.name)
    mode, minutes = room.mode, room.minutes
    logger.info(
        "starting interview room=%s mode=%s minutes=%d", ctx.room.name, mode.key.value, minutes
    )

    # Reuse the VAD the worker loaded during prewarm (see agent.py).
    session = build_session(settings, vad=ctx.proc.userdata.get("vad"))

    # Record the conversation as it happens, then score it once the call ends.
    recorder = TranscriptRecorder()
    recorder.attach(session)
    ctx.add_shutdown_callback(lambda: _score_interview(recorder, mode, ctx.room.name))

    # The API snapshots the candidate's resume onto the interview when the token
    # is issued, so the agent only needs the room name to find it.
    resume_text = await asyncio.to_thread(get_interview_resume, ctx.room.name)
    if resume_text:
        logger.info("interviewing against a resume (%d chars)", len(resume_text))

    interviewer = Interviewer(mode, resume_text)
    await session.start(interviewer, room=ctx.room)

    # Let the interviewer speak first — the "incoming call" opening line.
    await session.generate_reply(instructions=mode.opening)

    # Give the interview an ending: wrap up near the cap, then shut down (which
    # is what kicks off scoring). Runs in the background so hanging up still
    # works normally; the task is cancelled with the job.
    #
    # The reference is deliberate: asyncio only holds a weak reference to running
    # tasks, so a bare create_task() can be garbage-collected mid-interview and
    # the clock would silently never fire.
    clock = asyncio.create_task(
        run_interview_clock(
            session,
            interviewer,
            mode,
            minutes,
            on_finished=lambda: ctx.shutdown("interview complete"),
        )
    )
    ctx.add_shutdown_callback(lambda: _cancel(clock))


async def _cancel(task: asyncio.Task[None]) -> None:
    """Stop the interview clock when the candidate hangs up first."""
    task.cancel()


async def _score_interview(recorder: TranscriptRecorder, mode: InterviewMode, room: str) -> None:
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
