"""The LiveKit worker entrypoint: one job == one interview session."""

from __future__ import annotations

import logging

from livekit.agents import JobContext

from viva.agent.interviewer import Interviewer
from viva.agent.session import build_session
from viva.config import get_settings
from viva.interview.modes import get_mode

logger = logging.getLogger("viva.agent")


async def entrypoint(ctx: JobContext) -> None:
    """Connect to the room, start the interviewer, and open with a greeting."""
    settings = get_settings()

    # TODO(client): read the requested mode from room/participant metadata.
    mode = get_mode(settings.default_mode)
    logger.info("starting interview mode=%s", mode.key.value)

    await ctx.connect()

    session = build_session(settings)
    await session.start(Interviewer(mode), room=ctx.room)

    # Let the interviewer speak first — the "incoming call" opening line.
    await session.generate_reply(instructions=mode.opening)
