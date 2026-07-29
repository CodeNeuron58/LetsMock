"""Turn an uploaded resume PDF into text the interviewer can grill.

Deliberately small: extract the words, tidy the whitespace, cap the length. No
parsing into structured fields — the LLM reads prose perfectly well, and every
resume is laid out differently.
"""

from __future__ import annotations

import io
import logging
import re

from pypdf import PdfReader

logger = logging.getLogger("viva.interview.resume")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB — a resume PDF is far smaller
MAX_PAGES = 6
# Roughly 4-5k words: comfortably more than any real resume, and small enough
# that the interviewer's context stays cheap.
MAX_CHARS = 15_000


class ResumeError(ValueError):
    """The upload could not be turned into usable resume text."""


def extract_resume_text(data: bytes) -> str:
    """Extract plain text from a resume PDF. Raises `ResumeError` if unusable."""
    if not data:
        raise ResumeError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ResumeError("That file is too large — please upload a PDF under 5 MB.")

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = reader.pages[:MAX_PAGES]
        text = "\n".join(page.extract_text() or "" for page in pages)
    except Exception as e:  # malformed/encrypted PDFs land here
        logger.warning("could not read resume PDF: %s", e)
        raise ResumeError("That PDF could not be read. Try exporting it again.") from e

    text = _tidy(text)
    if len(text) < 100:
        # Almost always a scanned/image-only resume, which has no text layer.
        raise ResumeError(
            "No text could be read from that PDF. If it is a scan, please upload a "
            "text-based PDF instead."
        )
    return text[:MAX_CHARS]


def _tidy(text: str) -> str:
    """Collapse the ragged whitespace PDF extraction produces."""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()
