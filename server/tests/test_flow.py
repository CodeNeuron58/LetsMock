"""The interview clock — what gives an interview an ending."""

from __future__ import annotations

import asyncio

import pytest

from viva.interview import flow
from viva.interview.modes import DEFAULT_MINUTES, get_mode, parse_room_name, room_name_for


class _FakeAgent:
    def __init__(self):
        self.instructions = None

    async def update_instructions(self, text):
        self.instructions = text


class _FakeSession:
    def __init__(self):
        self.drained = False

    async def drain(self):
        self.drained = True


@pytest.mark.parametrize(("mode", "minutes"), [("hr", 5), ("sde", 15), ("resume", 5)])
def test_room_name_round_trips_mode_and_length(mode, minutes):
    info = parse_room_name(room_name_for(mode, minutes))

    assert info.mode.key.value == mode
    assert info.minutes == minutes


def test_unrecognised_room_names_fall_back_safely():
    """`agent.py console` uses a mock room that this never created."""
    info = parse_room_name("mock-job-abc123")

    assert info.mode.key.value == "hr"
    assert info.minutes == DEFAULT_MINUTES


def test_wrap_up_time_is_proportional_for_short_interviews():
    assert flow.wrap_up_lead(5) == 75.0  # 25% of five minutes


def test_wrap_up_time_is_capped_for_long_interviews():
    """A long interview should not spend minutes saying goodbye."""
    assert flow.wrap_up_lead(60) == flow.MAX_WRAP_UP_LEAD_SECONDS


def test_clock_asks_for_a_wrap_up_then_ends_the_interview(monkeypatch):
    monkeypatch.setattr(flow, "MAX_WRAP_UP_LEAD_SECONDS", 0.2)
    agent, session, finished = _FakeAgent(), _FakeSession(), []

    asyncio.run(
        flow.run_interview_clock(
            session,
            agent,
            get_mode("hr"),
            minutes=0.01,  # ~0.6s so the test is fast
            on_finished=lambda: finished.append(True),
        )
    )

    assert "close the interview" in agent.instructions
    assert session.drained  # closing words are allowed to finish
    assert finished == [True]


def test_hanging_up_first_cancels_the_clock():
    """Otherwise the job would be shut down twice."""
    agent, session, finished = _FakeAgent(), _FakeSession(), []

    async def scenario():
        task = asyncio.create_task(
            flow.run_interview_clock(
                session, agent, get_mode("hr"), minutes=5, on_finished=lambda: finished.append(True)
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert finished == []
