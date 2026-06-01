"""Schema defaults and the cover-letter contact fallback."""
from __future__ import annotations

from app.schema import Contact, CoverLetter, ResumeContent, TailoredDocs


def test_contact_defaults():
    c = Contact(name="Jane Doe")
    assert c.email == ""
    assert c.phone == ""
    assert c.links == []


def test_fallback_signs_cover_letter_when_signature_missing():
    docs = TailoredDocs(
        resume=ResumeContent(contact=Contact(name="Jane Doe")),
        cover_letter=CoverLetter(),
    )
    assert docs.cover_letter.signature == ""
    docs.with_contact_fallback()
    assert docs.cover_letter.signature == "Jane Doe"


def test_fallback_preserves_existing_signature():
    docs = TailoredDocs(
        resume=ResumeContent(contact=Contact(name="Jane Doe")),
        cover_letter=CoverLetter(signature="J. Doe"),
    )
    docs.with_contact_fallback()
    assert docs.cover_letter.signature == "J. Doe"
