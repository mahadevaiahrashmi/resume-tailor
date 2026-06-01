"""Structured representation of the tailored documents the LLM must return.

The LLM is asked to emit JSON matching `TailoredDocs`. The renderers
(`render_pdf`, `render_docx`) consume these models, so this schema is the single
contract between the model output and the document layout.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    # Display links without scheme, e.g. "linkedin.com/in/jane", "github.com/jane".
    links: list[str] = Field(default_factory=list)


class SkillLine(BaseModel):
    # A labelled row in the Technical Skills section.
    label: str  # e.g. "Languages & ML"
    items: str  # e.g. "Python, SQL, PyTorch, TensorFlow"


class ExperienceItem(BaseModel):
    company: str
    title: str
    dates: str  # free text, e.g. "Jan 2025 – Jul 2025"
    bullets: list[str] = Field(default_factory=list)


class ResumeContent(BaseModel):
    contact: Contact
    summary: str = ""
    skills: list[SkillLine] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)  # one line each


class CoverLetter(BaseModel):
    date: str = ""
    recipient: list[str] = Field(default_factory=list)  # e.g. ["Hiring Manager", "Acme", "City"]
    salutation: str = "Dear Hiring Manager,"
    paragraphs: list[str] = Field(default_factory=list)
    closing: str = "Sincerely,"
    signature: str = ""  # signed name


class TailoredDocs(BaseModel):
    resume: ResumeContent
    cover_letter: CoverLetter

    def with_contact_fallback(self) -> "TailoredDocs":
        """Ensure the cover letter is signed and dated even if the model omitted it."""
        if not self.cover_letter.signature:
            self.cover_letter.signature = self.resume.contact.name
        return self
