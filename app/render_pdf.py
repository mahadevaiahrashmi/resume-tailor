"""Render TailoredDocs to 1-page A4 PDFs with reportlab.

Layout mirrors the DOCX renderer: navy name, ruled section headings, a labelled
skills block, role rows with right-aligned dates, and bullet lists. An auto-fit
loop shrinks typography in small steps until the content fits a single page.
"""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .schema import Contact, CoverLetter, ResumeContent

NAVY = HexColor("#1F3B5B")
RULE = HexColor("#2E5A88")
GRAY = HexColor("#555555")

PAGE_W, PAGE_H = A4
LM = RM = 42
CONTENT_W = PAGE_W - LM - RM

# Scales tried by the resume auto-fit loop (largest first).
RESUME_SCALES = [1.0, 0.96, 0.92, 0.88, 0.84, 0.8, 0.76]


def esc(text: str) -> str:
    return escape(text or "")


def _join_contact(c: Contact) -> str:
    parts = [c.email, c.phone, *c.links]
    return "&nbsp;&nbsp;|&nbsp;&nbsp;".join(esc(p) for p in parts if p)


def _resume_styles(s: float) -> dict:
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=16 * s,
                               textColor=NAVY, alignment=TA_CENTER, spaceAfter=2 * s,
                               leading=18 * s),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=8.5 * s,
                                  textColor=GRAY, alignment=TA_CENTER, spaceAfter=1,
                                  leading=11 * s),
        "heading": ParagraphStyle("heading", fontName="Helvetica-Bold",
                                  fontSize=10.5 * s, textColor=NAVY, spaceBefore=6 * s,
                                  spaceAfter=1, leading=12 * s),
        "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=9.2 * s,
                                  leading=11 * s, alignment=TA_JUSTIFY, spaceAfter=1),
        "skill": ParagraphStyle("skill", fontName="Helvetica", fontSize=9.2 * s,
                               leading=11 * s, alignment=TA_LEFT, spaceAfter=1.5),
        "left": ParagraphStyle("left", fontName="Helvetica", fontSize=10 * s,
                              leading=12 * s),
        "date": ParagraphStyle("date", fontName="Helvetica", fontSize=9 * s,
                              textColor=GRAY, alignment=TA_RIGHT, leading=12 * s),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.2 * s,
                                leading=11 * s),
    }


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=1,
                      spaceAfter=2, lineCap="round")


def _section(title: str, st: dict) -> list:
    return [Paragraph(esc(title).upper(), st["heading"]), _hr()]


def _role(company: str, title: str, dates: str, st: dict) -> Table:
    label = f"<b>{esc(company)}</b>"
    if title:
        label += f"&nbsp;&nbsp;&mdash;&nbsp;&nbsp;{esc(title)}"
    left = Paragraph(label, st["left"])
    right = Paragraph(esc(dates), st["date"])
    t = Table([[left, right]], colWidths=[CONTENT_W * 0.70, CONTENT_W * 0.30])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _bullets(items: list[str], st: dict) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(esc(t), st["bullet"]), value="•", leftIndent=14,
                  spaceBefore=0, spaceAfter=1) for t in items],
        bulletType="bullet", start="•", leftIndent=12, bulletFontSize=10 * st["bullet"].fontSize / 9.2,
    )


def _resume_flowables(resume: ResumeContent, st: dict) -> list:
    flow: list = [Paragraph(esc(resume.contact.name), st["name"])]
    contact = _join_contact(resume.contact)
    if contact:
        flow.append(Paragraph(contact, st["contact"]))

    if resume.summary:
        flow += _section("Summary", st)
        flow.append(Paragraph(esc(resume.summary), st["summary"]))

    if resume.skills:
        flow += _section("Technical Skills", st)
        for s in resume.skills:
            flow.append(Paragraph(f"<b>{esc(s.label)}:</b>&nbsp;&nbsp;{esc(s.items)}", st["skill"]))

    if resume.experience:
        flow += _section("Experience", st)
        for e in resume.experience:
            flow.append(_role(e.company, e.title, e.dates, st))
            if e.bullets:
                flow.append(_bullets(e.bullets, st))

    if resume.education:
        flow += _section("Education", st)
        for line in resume.education:
            flow.append(Paragraph(esc(line), st["summary"]))
    return flow


def _build_to_bytes(flowables: list, top: float, bottom: float) -> tuple[int, bytes]:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=LM, rightMargin=RM,
                            topMargin=top, bottomMargin=bottom,
                            title="Resume", author="Resume Tailor")
    doc.build(flowables)
    return doc.page, buf.getvalue()


def _resume_pdf_at(resume: ResumeContent, scale: float) -> tuple[int, bytes]:
    st = _resume_styles(scale)
    return _build_to_bytes(_resume_flowables(resume, st), top=26, bottom=22)


def resume_fit_scale(resume: ResumeContent) -> float:
    """The largest `RESUME_SCALES` value at which the resume fits one page.

    Exposed so the DOCX renderer can mirror the PDF's one-page decision (Word
    has no layout engine of its own to measure against).
    """
    for scale in RESUME_SCALES:
        pages, _ = _resume_pdf_at(resume, scale)
        if pages <= 1:
            return scale
    return RESUME_SCALES[-1]


def render_resume_pdf(resume: ResumeContent, out_path: str, scale: float | None = None) -> str:
    """Write the resume PDF. With `scale=None`, shrink type until it fits one page."""
    if scale is None:
        last_bytes = b""
        for s in RESUME_SCALES:
            pages, data = _resume_pdf_at(resume, s)
            last_bytes = data
            if pages <= 1:
                break
    else:
        _, last_bytes = _resume_pdf_at(resume, scale)
    with open(out_path, "wb") as fh:
        fh.write(last_bytes)
    return out_path


# ---------------- COVER LETTER ----------------

def _cover_styles(s: float) -> dict:
    return {
        "name": ParagraphStyle("clname", fontName="Helvetica-Bold", fontSize=16 * s,
                               textColor=NAVY, spaceAfter=2, leading=19 * s),
        "contact": ParagraphStyle("clcontact", fontName="Helvetica", fontSize=9 * s,
                                  textColor=GRAY, spaceAfter=16 * s, leading=12 * s),
        "meta": ParagraphStyle("clmeta", fontName="Helvetica", fontSize=11 * s,
                              leading=15 * s),
        "body": ParagraphStyle("clbody", fontName="Helvetica", fontSize=11 * s,
                              leading=15.5 * s, alignment=TA_JUSTIFY, spaceAfter=11 * s),
    }


def _cover_flowables(cl: CoverLetter, contact: Contact, st: dict) -> list:
    flow: list = [Paragraph(esc(contact.name), st["name"])]
    line = _join_contact(contact)
    if line:
        flow.append(Paragraph(line, st["contact"]))
    if cl.date:
        flow.append(Paragraph(esc(cl.date), st["meta"]))
        flow.append(Spacer(1, 10))
    for r in cl.recipient:
        if r:
            flow.append(Paragraph(esc(r), st["meta"]))
    flow.append(Spacer(1, 12))
    if cl.salutation:
        flow.append(Paragraph(esc(cl.salutation), st["meta"]))
        flow.append(Spacer(1, 10))
    for para in cl.paragraphs:
        flow.append(Paragraph(esc(para), st["body"]))
    flow.append(Spacer(1, 12))
    if cl.closing:
        flow.append(Paragraph(esc(cl.closing), st["meta"]))
    flow.append(Spacer(1, 14))
    if cl.signature:
        flow.append(Paragraph(f"<b>{esc(cl.signature)}</b>", st["meta"]))
    return flow


def _cover_pdf_at(cl: CoverLetter, contact: Contact, scale: float) -> tuple[int, bytes]:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=72, rightMargin=72,
                            topMargin=72, bottomMargin=54,
                            title="Cover Letter", author="Resume Tailor")
    doc.build(_cover_flowables(cl, contact, _cover_styles(scale)))
    return doc.page, buf.getvalue()


def cover_letter_fit_scale(cl: CoverLetter, contact: Contact) -> float:
    """The largest `RESUME_SCALES` value at which the cover letter fits one page."""
    for scale in RESUME_SCALES:
        pages, _ = _cover_pdf_at(cl, contact, scale)
        if pages <= 1:
            return scale
    return RESUME_SCALES[-1]


def render_cover_letter_pdf(cl: CoverLetter, contact: Contact, out_path: str,
                            scale: float | None = None) -> str:
    if scale is None:
        last_bytes = b""
        for s in RESUME_SCALES:
            pages, data = _cover_pdf_at(cl, contact, s)
            last_bytes = data
            if pages <= 1:
                break
    else:
        _, last_bytes = _cover_pdf_at(cl, contact, scale)
    with open(out_path, "wb") as fh:
        fh.write(last_bytes)
    return out_path
