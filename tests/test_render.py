"""Renderers: PDFs must be exactly one page; DOCX must be valid and complete."""
from __future__ import annotations

import re

from docx import Document

from app.render_docx import render_cover_letter_docx, render_resume_docx
from app.render_pdf import render_cover_letter_pdf, render_resume_pdf


def _pdf_page_count(data: bytes) -> int:
    """Count page objects in a reportlab PDF.

    reportlab writes each page as an uncompressed `/Type /Page` object and one
    `/Type /Pages` root; the `\\b` keeps `/Pages` from matching `/Page`.
    """
    return len(re.findall(rb"/Type\s*/Page\b", data))


def _docx_text(path: str) -> str:
    return "\n".join(p.text for p in Document(path).paragraphs)


def test_resume_pdf_is_one_page(docs, tmp_path):
    out = tmp_path / "resume.pdf"
    render_resume_pdf(docs.resume, str(out))
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert _pdf_page_count(data) == 1


def test_dense_resume_still_one_page(dense_docs, tmp_path):
    """Auto-fit must shrink a near-budget resume down to a single page."""
    out = tmp_path / "dense.pdf"
    render_resume_pdf(dense_docs.resume, str(out))
    assert _pdf_page_count(out.read_bytes()) == 1


def test_cover_letter_pdf_is_one_page(docs, tmp_path):
    out = tmp_path / "cover.pdf"
    render_cover_letter_pdf(docs.cover_letter, docs.resume.contact, str(out))
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert _pdf_page_count(data) == 1


def test_resume_docx_is_valid_and_complete(docs, tmp_path):
    out = tmp_path / "resume.docx"
    render_resume_docx(docs.resume, str(out))
    text = _docx_text(str(out))
    assert "Rashmi Mahadevaiah" in text
    assert "EXPERIENCE" in text          # headings are upper-cased
    assert "Languages & ML:" in text     # skill label rendered with colon
    assert "Built a RAG pipeline serving 2M requests/day." in text


def test_cover_letter_docx_is_valid_and_complete(docs, tmp_path):
    out = tmp_path / "cover.docx"
    render_cover_letter_docx(docs.cover_letter, docs.resume.contact, str(out))
    text = _docx_text(str(out))
    assert "Rashmi Mahadevaiah" in text
    assert "Dear Hiring Manager," in text
    assert "Sincerely," in text


def test_cover_letter_docx_falls_back_to_contact_name(docs, tmp_path):
    docs.cover_letter.signature = ""
    out = tmp_path / "cover.docx"
    render_cover_letter_docx(docs.cover_letter, docs.resume.contact, str(out))
    # signature line falls back to the contact name
    assert "Rashmi Mahadevaiah" in _docx_text(str(out))
