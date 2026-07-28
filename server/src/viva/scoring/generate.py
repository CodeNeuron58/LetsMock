"""Turn an interview transcript into a scorecard: deterministic metrics from code,
qualitative judgement from the LLM (structured JSON -> Pydantic)."""

from __future__ import annotations

import json
import logging

from groq import Groq
from pydantic import ValidationError

from viva.config import get_settings
from viva.interview.modes import InterviewMode
from viva.scoring.metrics import compute_metrics
from viva.scoring.schema import Assessment, Scorecard, SpeechMetrics
from viva.scoring.transcript import Transcript

logger = logging.getLogger("viva.scoring")

_SYSTEM = (
    "You are a demanding senior interviewer writing a candid post-interview "
    "scorecard for a candidate practising for a real, high-stakes interview. Be "
    "specific and honest — reference what they actually said. Do not be gentle; "
    "this is practice and vague praise helps no one. Score strictly: a 7+ means "
    "genuinely strong."
)

_USER_TEMPLATE = """\
This was a {mode_name} round ({mode_focus}).

Delivery metrics (already measured in code — use them in your judgement, do NOT
recompute): ~{words} words spoken at {wpm} words/min, {fillers} filler words.

Transcript:
{transcript}

Return ONLY a JSON object matching this schema exactly (no prose, no markdown):
{schema}"""


def generate_scorecard(transcript: Transcript, mode: InterviewMode) -> Scorecard:
    """Full pipeline: metrics (code) + assessment (LLM) -> Scorecard."""
    metrics = compute_metrics(transcript)
    assessment = _assess(transcript, mode, metrics)
    return Scorecard(
        mode=mode.key.value,
        assessment=assessment,
        metrics=metrics,
        transcript=transcript.as_text(),
    )


def _assess(
    transcript: Transcript,
    mode: InterviewMode,
    metrics: SpeechMetrics,
    *,
    retries: int = 1,
) -> Assessment:
    """Ask the LLM for the qualitative assessment as schema-validated JSON."""
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    user = _USER_TEMPLATE.format(
        mode_name=mode.display_name,
        mode_focus=mode.focus,
        words=metrics.candidate_word_count,
        wpm=metrics.words_per_minute,
        fillers=metrics.filler_word_count,
        transcript=transcript.as_text(),
        schema=json.dumps(Assessment.model_json_schema()),
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        resp = client.chat.completions.create(
            model=settings.scorecard_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = resp.choices[0].message.content or "{}"
        try:
            return Assessment.model_validate_json(content)
        except ValidationError as e:
            last_error = e
            logger.warning("scorecard JSON invalid (attempt %d): %s", attempt, e)
            messages += [
                {"role": "assistant", "content": content},
                {"role": "user", "content": f"That JSON was invalid: {e}. Return corrected JSON only."},
            ]
    raise RuntimeError(f"scorecard generation failed after {retries + 1} attempts: {last_error}")
