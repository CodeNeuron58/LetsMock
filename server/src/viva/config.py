"""Typed settings loaded from the environment / .env.

The LiveKit fields are optional here because this module is imported by tooling
that never connects. Note that `agent.py console` still needs them *set* to
something — the worker builds a LiveKit API client on startup even though it
never dials out — so `.env.example` ships dummy values for them.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Model providers (required) ---
    groq_api_key: str
    deepgram_api_key: str

    # --- LiveKit (optional for console; required for dev/prod workers) ---
    livekit_url: str | None = None
    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None

    # --- Models ---
    # STT: Deepgram Nova-3 (streaming = low latency; keeps filler words for the
    # scorecard; supports keyterm biasing for accents/domain terms).
    stt_model: str = "nova-3"
    llm_model: str = "llama-3.3-70b-versatile"
    tts_model: str = "aura-2-andromeda-en"

    # Stronger model for the async post-call scorecard (latency doesn't matter here).
    scorecard_model: str = "llama-3.3-70b-versatile"

    # Bias STT toward domain vocabulary — the fix for accent mishears where a
    # rare technical term loses to a common word ("Gemini" -> "Gmail",
    # "tool calling" -> "tool pulling"). Deepgram keyterm supports multi-word
    # phrases. Keep it focused; expand as new mangles show up in transcripts.
    stt_keyterms: list[str] = Field(
        default_factory=lambda: [
            # Interview / placement
            "role",
            "resume",
            "internship",
            "placement",
            "recruiter",
            "fresher",
            "SDE",
            "HR round",
            "behavioral",
            "STAR method",
            "CTC",
            "NQT",
            # Backend / infra
            "API",
            "REST",
            "GraphQL",
            "backend",
            "frontend",
            "microservices",
            "WebSocket",
            "Docker",
            "Kubernetes",
            "Postgres",
            "Redis",
            "DBMS",
            "latency",
            # AI / ML stack
            "LLM",
            "RAG",
            "embeddings",
            "vector database",
            "Pydantic",
            "FastAPI",
            "LangGraph",
            "cascade",
            "tool calling",
            "Gemini",
            "Whisper",
            "Silero",
            "Deepgram",
            "LiveKit",
            # Languages / product
            "Python",
            "TypeScript",
            "Yumii",
            "LetsMock",
            "startup",
        ]
    )

    # --- Turn-taking / barge-in tuning ---
    # The "patience" dials: how long to wait after speech before deciding the
    # candidate is done. Erring patient keeps us from cutting off nervous pauses.
    allow_interruptions: bool = True
    min_endpointing_delay: float = 0.5
    max_endpointing_delay: float = 6.0
    min_interruption_duration: float = 0.5

    # Where interviews and scorecards are stored. SQLite by default so there is
    # nothing to run locally; point at Postgres in production
    # (postgresql+psycopg://user:pass@host/db) — no code changes needed.
    database_url: str = "sqlite:///./viva.db"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton (reads env / .env once)."""
    return Settings()  # type: ignore[call-arg]  # fields come from the environment
