"""Database engine and tables.

SQLite by default (zero setup); the same models run on Postgres by pointing
`database_url` at it. The LiveKit room name is the primary key: the client
already knows it from `POST /session`, so no extra id has to be passed around.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from sqlalchemy import DateTime, Engine, Enum, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from viva.config import get_settings


class Base(DeclarativeBase):
    pass


class InterviewStatus(str, enum.Enum):
    pending = "pending"  # created, interview not finished
    scored = "scored"  # scorecard ready
    failed = "failed"  # scoring failed; the call still happened


class Interview(Base):
    __tablename__ = "interviews"

    room: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(16))
    # RevenueCat app user id. Free-tier quota is counted against this.
    user_id: Mapped[str | None] = mapped_column(String(128), index=True, default=None)
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus), default=InterviewStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Full Scorecard as JSON — the schema is owned by Pydantic, not the database.
    scorecard: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


@lru_cache
def get_engine() -> Engine:
    """Process-wide engine. The agent worker and the API server each hold their
    own; with SQLite they share the file, so writes are short and serialised."""
    url = get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(engine)  # tables are created on first use
    return engine


def new_session() -> Session:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)()
