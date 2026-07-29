"""Give the interview a shape: it starts, it runs, and it *ends*.

Without this the agent keeps interviewing until the candidate hangs up, and the
free-tier length cap the API hands out is never enforced.

Two beats rather than a hard cut-off:

* **Wrap-up** — shortly before time is up the agent's instructions are swapped
  for a closing brief. Nothing is interrupted; the interviewer simply closes on
  its next turn, the way a real one would.
* **Hard stop** — at the cap, whatever is being said is allowed to finish
  (`drain`) and the job shuts down, which is what triggers scoring.
"""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import Agent, AgentSession

from viva.interview.modes import WRAP_UP_INSTRUCTIONS, InterviewMode

logger = logging.getLogger("viva.interview.flow")

# How long before the cap to ask for a close, and how long to allow for the
# closing words once time is up.
MAX_WRAP_UP_LEAD_SECONDS = 90.0
WRAP_UP_FRACTION = 0.25
HARD_STOP_GRACE_SECONDS = 20.0


def wrap_up_lead(minutes: int) -> float:
    """Seconds of closing time to reserve — proportional for short interviews,
    capped so a long one does not spend minutes saying goodbye."""
    return min(MAX_WRAP_UP_LEAD_SECONDS, minutes * 60 * WRAP_UP_FRACTION)


async def run_interview_clock(
    session: AgentSession,
    agent: Agent,
    mode: InterviewMode,
    minutes: int,
    on_finished: callable,
) -> None:
    """Run the interview's clock. Cancelled automatically if the candidate
    hangs up first."""
    total = minutes * 60
    lead = wrap_up_lead(minutes)

    try:
        await asyncio.sleep(max(0.0, total - lead))
        logger.info("interview wrapping up mode=%s (%.0fs left)", mode.key.value, lead)
        # Swap the brief rather than speaking over them: the interviewer closes
        # on its own next turn.
        await agent.update_instructions(
            f"{mode.instructions()}\n\n--- Time check ---\n{WRAP_UP_INSTRUCTIONS}"
        )

        await asyncio.sleep(lead)
        logger.info("interview time is up mode=%s", mode.key.value)
        # Let any closing words finish before tearing the session down.
        await asyncio.wait_for(session.drain(), timeout=HARD_STOP_GRACE_SECONDS)
    except asyncio.CancelledError:
        raise  # candidate hung up first; nothing to do
    except TimeoutError:
        logger.warning("drain timed out at the cap; ending anyway")
    except Exception:
        logger.exception("interview clock failed; ending the interview")

    on_finished()
