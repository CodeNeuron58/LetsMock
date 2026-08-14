"""The free tier — the rules that keep voice costs from outrunning revenue."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from viva.quota import check_quota
from viva.storage.models import Interview, new_session
from viva.storage.store import create_interview


def test_first_interview_is_free():
    decision = check_quota("user_A", is_pro=False)
    assert decision.allowed
    assert decision.minutes == 5


def test_second_interview_in_the_same_week_is_blocked():
    create_interview("viva-hr-1", "hr", user_id="user_A")

    decision = check_quota("user_A", is_pro=False)

    assert not decision.allowed
    assert "week" in decision.reason.lower()
    assert decision.next_available is not None


def test_free_interview_returns_after_the_window():
    create_interview("viva-hr-1", "hr", user_id="user_A")
    with new_session() as db:
        db.get(Interview, "viva-hr-1").created_at = datetime.now(UTC) - timedelta(days=8)
        db.commit()

    assert check_quota("user_A", is_pro=False).allowed


def test_pro_is_never_blocked_and_gets_longer_interviews():
    create_interview("viva-hr-1", "hr", user_id="user_A")

    decision = check_quota("user_A", is_pro=True)

    assert decision.allowed
    assert decision.minutes == 15


def test_quota_is_counted_per_user():
    create_interview("viva-hr-1", "hr", user_id="user_A")

    assert not check_quota("user_A", is_pro=False).allowed
    assert check_quota("user_B", is_pro=False).allowed


def test_anonymous_request_is_treated_as_a_first_time_user():
    assert check_quota(None, is_pro=False).allowed
