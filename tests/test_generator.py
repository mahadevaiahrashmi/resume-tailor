"""Generator: JSON extraction, schema parsing, and end-to-end orchestration."""
from __future__ import annotations

import json

import pytest

from app.generator import (
    GenerationError,
    extract_json,
    generate_documents,
    parse_docs,
)
from app.providers import ProviderError


def test_extract_json_plain():
    assert json.loads(extract_json('{"a": 1}'))["a"] == 1


def test_extract_json_strips_code_fence():
    fenced = '```json\n{"a": 2}\n```'
    assert json.loads(extract_json(fenced))["a"] == 2


def test_extract_json_ignores_surrounding_prose():
    prosed = 'Sure, here you go:\n{"a": 3}\nHope that helps!'
    assert json.loads(extract_json(prosed))["a"] == 3


def test_extract_json_honours_braces_inside_strings():
    nested = '{"a": {"b": [1, 2]}, "c": "}"}'
    parsed = json.loads(extract_json(nested))
    assert parsed["c"] == "}"
    assert parsed["a"]["b"] == [1, 2]


def test_extract_json_raises_without_object():
    with pytest.raises(GenerationError):
        extract_json("no json here at all")


def test_parse_docs_applies_contact_fallback():
    raw = json.dumps({"resume": {"contact": {"name": "X"}}, "cover_letter": {}})
    docs = parse_docs(raw)
    assert docs.resume.contact.name == "X"
    assert docs.cover_letter.signature == "X"


def test_parse_docs_tolerates_control_chars_in_strings():
    # Local models often emit literal newlines inside string values; strict=False
    # must accept them rather than raising "Invalid control character".
    raw = '{"resume": {"contact": {"name": "X"}, "summary": "line one\nline two"}, "cover_letter": {}}'
    docs = parse_docs(raw)
    assert "line one" in docs.resume.summary
    assert "line two" in docs.resume.summary


def test_parse_docs_rejects_invalid_json():
    with pytest.raises(GenerationError):
        parse_docs("{ this is not valid json }")


def test_parse_docs_rejects_schema_mismatch():
    # resume present but missing the required contact object
    with pytest.raises(GenerationError):
        parse_docs(json.dumps({"resume": {}, "cover_letter": {}}))


def test_generate_documents_rejects_empty_jd(sample_resume):
    with pytest.raises(GenerationError):
        generate_documents("", sample_resume)


def test_generate_documents_rejects_empty_resume(sample_jd):
    with pytest.raises(GenerationError):
        generate_documents(sample_jd, "   ")


def test_generate_documents_with_mock(sample_jd, sample_resume):
    docs = generate_documents(sample_jd, sample_resume, provider_name="mock")
    assert docs.resume.contact.name == "Rashmi Mahadevaiah"
    assert docs.resume.experience  # at least one role parsed
    assert docs.cover_letter.signature == docs.resume.contact.name


def test_generate_documents_unavailable_provider_raises_hint(
    sample_jd, sample_resume, monkeypatch
):
    monkeypatch.setattr("app.providers.gemini_cli.cli_exists", lambda _b: False)
    with pytest.raises(GenerationError) as ei:
        generate_documents(sample_jd, sample_resume, provider_name="gemini")
    assert "Gemini CLI not found" in str(ei.value)


def test_generate_documents_wraps_provider_error(
    sample_jd, sample_resume, monkeypatch
):
    monkeypatch.setattr("app.providers.gemini_cli.cli_exists", lambda _b: True)

    def boom(*_a, **_k):
        raise ProviderError("CLI blew up")

    monkeypatch.setattr("app.providers.gemini_cli.run_cli", boom)
    with pytest.raises(GenerationError) as ei:
        generate_documents(sample_jd, sample_resume, provider_name="gemini")
    assert "CLI blew up" in str(ei.value)
