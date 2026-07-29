"""The HTTP surface the app talks to."""

from __future__ import annotations

from viva.interview.modes import parse_room_name
from viva.scoring.schema import Assessment, Scorecard, SpeechMetrics
from viva.storage import create_interview, get_interview, mark_failed, save_scorecard


def _scorecard(mode: str = "hr") -> Scorecard:
    return Scorecard(
        mode=mode,
        assessment=Assessment(
            overall_score=6.5,
            summary="Decent structure, thin on specifics.",
            strengths=["Clear motivation"],
            weaknesses=["Vague examples"],
            structure_note="Partial STAR usage.",
        ),
        metrics=SpeechMetrics(words_per_minute=103.4, filler_word_count=8),
        transcript="INTERVIEWER: Hi\nCANDIDATE: Hello",
    )


def test_health(client):
    assert client.get("/health").json() == {"ok": True}


def test_session_returns_a_token_and_the_free_length_cap(client):
    res = client.post("/session", json={"mode": "hr", "user_id": "u1", "is_pro": False})

    assert res.status_code == 200
    body = res.json()
    assert body["minutes"] == 5
    assert body["token"]
    assert parse_room_name(body["room"]).mode.key.value == "hr"


def test_session_bakes_the_length_cap_into_the_room_name(client):
    """The agent has only the room name to work from, so the cap rides in it."""
    res = client.post("/session", json={"mode": "sde", "user_id": "u1", "is_pro": True})

    assert parse_room_name(res.json()["room"]).minutes == 15


def test_unknown_mode_falls_back_to_hr(client):
    res = client.post("/session", json={"mode": "nonsense", "user_id": "u1"})

    assert res.status_code == 200
    assert res.json()["mode"] == "hr"


def test_exhausted_free_tier_returns_402_so_the_client_can_show_the_paywall(client):
    client.post("/session", json={"mode": "hr", "user_id": "u1", "is_pro": False})

    res = client.post("/session", json={"mode": "hr", "user_id": "u1", "is_pro": False})

    assert res.status_code == 402
    assert res.json()["detail"]["reason"]


def test_scorecard_is_404_for_an_unknown_room(client):
    assert client.get("/scorecard/viva-hr-nope").status_code == 404


def test_scorecard_is_202_while_the_interview_is_still_running(client):
    create_interview("viva-hr-1", "hr")

    res = client.get("/scorecard/viva-hr-1")

    assert res.status_code == 202
    assert res.json()["status"] == "pending"
    assert res.json()["scorecard"] is None


def test_scorecard_is_returned_once_scoring_finishes(client):
    create_interview("viva-hr-1", "hr")
    save_scorecard("viva-hr-1", _scorecard())

    res = client.get("/scorecard/viva-hr-1")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "scored"
    assert body["scorecard"]["assessment"]["overall_score"] == 6.5
    # The client re-parses this into its own model, so it must round-trip.
    assert Scorecard.model_validate(body["scorecard"]).metrics.words_per_minute == 103.4


def test_failed_scoring_is_reported_rather_than_left_pending(client):
    create_interview("viva-hr-1", "hr")
    mark_failed("viva-hr-1")

    res = client.get("/scorecard/viva-hr-1")

    assert res.status_code == 200
    assert res.json()["status"] == "failed"


def test_scorecards_from_rooms_the_api_never_issued_are_kept(client):
    """Console runs and directly dispatched jobs still produce real interviews."""
    save_scorecard("mock-job-console", _scorecard())

    assert get_interview("mock-job-console") is not None
    assert client.get("/scorecard/mock-job-console").status_code == 200
