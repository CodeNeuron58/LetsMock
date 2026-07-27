"""The LiveKit worker entrypoint: one job == one interview session."""

from __future__ import annotations

import logging

from livekit.agents import JobContext

from viva.agent.interviewer import Interviewer
from viva.agent.session import build_session
from viva.config import get_settings
from viva.interview.modes import mode_from_room_name

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
    await session.start(Interviewer(mode), room=ctx.room)

    # Let the interviewer speak first — the "incoming call" opening line.
    await session.generate_reply(instructions=mode.opening)
