"""Shared fixtures.

Every test runs against a throwaway SQLite file so nothing touches the real
database, and so the engine cache in `viva.storage.models` is rebuilt per test.
"""

from __future__ import annotations

import os

import pytest

# Set before anything imports viva.config — Settings reads the environment once.
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-key")
os.environ.setdefault("LIVEKIT_URL", "ws://localhost:7880")
os.environ.setdefault("LIVEKIT_API_KEY", "devkey")
# >=32 bytes: JWT signing warns below that.
os.environ.setdefault("LIVEKIT_API_SECRET", "devsecret_for_tests_000000000000000000")


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at its own empty database."""
    from viva.config import get_settings
    from viva.storage import models

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    models.get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    models.get_engine.cache_clear()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from viva.api import app

    return TestClient(app)


@pytest.fixture
def resume_pdf() -> bytes:
    """A small but realistic resume PDF."""
    import io

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    lines = [
        "Biprayan Choudhuri",
        "AI Engineer - Indian Institute of Technology Guwahati",
        "",
        "PROJECTS",
        "Yumii - Open-Source Local Voice AI Companion",
        "Built a real-time voice companion: Silero VAD, Whisper STT, a LangGraph",
        "agent and streaming TTS, supporting barge-in interruption.",
        "",
        "Multi-Agent Orchestration System",
        "A master orchestrator routes tasks via structured JSON reasoning",
        "across five specialised agents, with per-node context budgets.",
        "",
        "OPEN SOURCE",
        "Pydantic (22K stars) - merged PR #13314 fixing validation logic.",
    ]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
    c.save()
    return buf.getvalue()
