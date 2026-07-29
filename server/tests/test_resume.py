"""Resume Grill — parsing the PDF and getting it in front of the interviewer."""

from __future__ import annotations

import io

import pytest
from pypdf import PdfWriter

from viva.interview.modes import get_mode
from viva.interview.resume import ResumeError, extract_resume_text
from viva.storage import get_interview


def _blank_pdf() -> bytes:
    """A PDF with pages but no text layer — i.e. what a scan looks like."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_extracts_text_from_a_resume_pdf(resume_pdf):
    text = extract_resume_text(resume_pdf)

    assert "Yumii" in text
    assert "Pydantic" in text


@pytest.mark.parametrize(
    ("label", "data"),
    [
        ("empty", b""),
        ("not a pdf", b"just some text, not a pdf at all"),
    ],
)
def test_unusable_uploads_are_rejected(label, data):
    with pytest.raises(ResumeError):
        extract_resume_text(data)


def test_scanned_pdf_gets_an_explanation_rather_than_a_generic_error():
    """An image-only resume is the most likely real-world failure."""
    with pytest.raises(ResumeError, match="scan"):
        extract_resume_text(_blank_pdf())


def test_oversized_upload_is_refused_before_parsing():
    with pytest.raises(ResumeError, match="too large"):
        extract_resume_text(b"x" * (6 * 1024 * 1024))


def test_upload_and_read_back(client, resume_pdf):
    res = client.post(
        "/resume",
        data={"user_id": "user_A"},
        files={"file": ("resume.pdf", resume_pdf, "application/pdf")},
    )

    assert res.status_code == 200
    assert res.json()["characters"] > 0
    assert client.get("/resume/user_A").json()["filename"] == "resume.pdf"


def test_no_resume_on_file_reads_back_as_null(client):
    assert client.get("/resume/nobody").json() is None


def test_non_pdf_upload_is_rejected(client):
    res = client.post(
        "/resume",
        data={"user_id": "user_A"},
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )

    assert res.status_code == 415


def test_resume_mode_snapshots_the_resume_onto_the_interview(client, resume_pdf):
    """Snapshotted, not looked up live, so a later upload cannot rewrite the
    context an earlier interview actually ran against."""
    client.post(
        "/resume",
        data={"user_id": "user_A"},
        files={"file": ("resume.pdf", resume_pdf, "application/pdf")},
    )

    res = client.post("/session", json={"mode": "resume", "user_id": "user_A", "is_pro": True})

    assert "Yumii" in get_interview(res.json()["room"]).resume_text


def test_other_modes_do_not_carry_the_resume(client, resume_pdf):
    client.post(
        "/resume",
        data={"user_id": "user_A"},
        files={"file": ("resume.pdf", resume_pdf, "application/pdf")},
    )

    res = client.post("/session", json={"mode": "hr", "user_id": "user_A", "is_pro": True})

    assert get_interview(res.json()["room"]).resume_text is None


def test_resume_mode_still_works_without_a_resume(client):
    res = client.post("/session", json={"mode": "resume", "user_id": "user_B", "is_pro": True})

    assert res.status_code == 200
    assert get_interview(res.json()["room"]).resume_text is None


def test_the_interviewer_prompt_contains_the_resume(resume_pdf):
    text = extract_resume_text(resume_pdf)

    prompt = get_mode("resume").instructions(text)

    assert "Yumii" in prompt
    assert "never read the resume" in prompt.lower()


def test_the_interviewer_prompt_is_valid_without_a_resume():
    prompt = get_mode("resume").instructions(None)

    assert "--- The candidate" not in prompt
    assert len(prompt) > 500
