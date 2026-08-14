"""Free-tier limits.

RevenueCat reports *whether* a user has Pro; it does not enforce anything. This
module is where the free tier actually lives.

The rule — **first interview free, then one per week** — is deliberate: each
interview costs real money in speech APIs (~70% of it TTS), so an unlimited
daily free tier could cost more per user than Pro earns. See `TODO.md` ->
*Pricing & unit economics*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from viva.storage.store import count_interviews, last_interview_at

FREE_WINDOW = timedelta(days=7)
FREE_MOCK_MINUTES = 5
PRO_MOCK_MINUTES = 15


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    minutes: int
    reason: str = ""
    next_available: datetime | None = None


def check_quota(user_id: str | None, is_pro: bool) -> QuotaDecision:
    """Decide whether this user may start an interview now."""
    if is_pro:
        return QuotaDecision(allowed=True, minutes=PRO_MOCK_MINUTES)

    if not user_id:
        # No identity to count against — treat as a first-time free user.
        return QuotaDecision(allowed=True, minutes=FREE_MOCK_MINUTES)

    if count_interviews(user_id) == 0:
        return QuotaDecision(allowed=True, minutes=FREE_MOCK_MINUTES, reason="first interview")

    last = last_interview_at(user_id)
    if last is None:
        return QuotaDecision(allowed=True, minutes=FREE_MOCK_MINUTES)

    # Rows written before timezone handling (or by SQLite) can come back naive.
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)

    next_available = last + FREE_WINDOW
    if datetime.now(UTC) >= next_available:
        return QuotaDecision(allowed=True, minutes=FREE_MOCK_MINUTES)

    return QuotaDecision(
        allowed=False,
        minutes=FREE_MOCK_MINUTES,
        reason="Free plan includes one interview per week. Upgrade for unlimited.",
        next_available=next_available,
    )
