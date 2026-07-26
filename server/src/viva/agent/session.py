"""Build the voice pipeline: STT -> LLM -> TTS with VAD + turn detection.

This is the "how the voice works" layer. The interview logic lives in the
`Agent`; this file is purely the tuned cascade and the barge-in behaviour.
"""

from __future__ import annotations

from livekit.agents import (
    AgentSession,
    EndpointingOptions,
    InterruptionOptions,
    TurnHandlingOptions,
)
from livekit.plugins import deepgram, groq, silero

# Local, on-device turn detector: predicts whether the candidate is actually
# done or just pausing to think. Runs offline (no cloud cost), which is why we
# keep it over `livekit.agents.inference.TurnDetector` (that one routes through
# LiveKit Cloud). Marked deprecated in this version but stable for the pin.
from livekit.plugins.turn_detector.english import EnglishModel

from viva.config import Settings


def build_session(settings: Settings) -> AgentSession:
    """Assemble the cascade with barge-in and patient turn-taking."""
    return AgentSession(
        # STT: Deepgram Nova-3 streaming. `filler_words` keeps the um/uh that
        # the scorecard counts; `keyterms` biases transcription toward interview
        # vocabulary so accents don't turn "role" into "rule".
        stt=deepgram.STT(
            model=settings.stt_model,
            interim_results=True,
            filler_words=True,
            keyterm=settings.stt_keyterms,
        ),
        llm=groq.LLM(model=settings.llm_model),
        tts=deepgram.TTS(model=settings.tts_model),
        vad=silero.VAD.load(),
        # TODO(week1): move VAD load into a prewarm_fnc so it isn't loaded per job.
        turn_handling=TurnHandlingOptions(
            turn_detection=EnglishModel(),
            # Dynamic endpointing: waits longer when the turn detector is unsure
            # the candidate is done (min_delay when confident, up to max_delay
            # for a nervous mid-thought pause).
            endpointing=EndpointingOptions(
                mode="dynamic",
                min_delay=settings.min_endpointing_delay,
                max_delay=settings.max_endpointing_delay,
            ),
            interruption=InterruptionOptions(
                enabled=settings.allow_interruptions,
                min_duration=settings.min_interruption_duration,
            ),
        ),
    )
