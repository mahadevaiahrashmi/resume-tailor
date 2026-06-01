"""Provider registry, CLI command construction, and the mock provider."""
from __future__ import annotations

import pytest

from app.generator import parse_docs
from app.prompts import build_prompt
from app.providers import (
    MockProvider,
    ProviderError,
    get_provider,
    list_providers,
)
from app.providers.gemini_cli import GeminiCLIProvider
from app.providers.ollama import OllamaProvider


def test_get_provider_defaults_to_mock():
    assert isinstance(get_provider(None), MockProvider)
    assert isinstance(get_provider("mock"), MockProvider)


def test_get_provider_passes_model_to_real_provider():
    g = get_provider("gemini", "gemini-2.5-flash")
    assert isinstance(g, GeminiCLIProvider)
    assert g.model == "gemini-2.5-flash"


def test_get_provider_unknown_raises():
    with pytest.raises(ProviderError):
        get_provider("nope")


def test_list_providers_shape():
    provs = list_providers()
    assert {p["name"] for p in provs} == {"gemini", "ollama", "mock"}
    assert all({"name", "label", "available"} <= set(p) for p in provs)
    mock = next(p for p in provs if p["name"] == "mock")
    assert mock["available"] is True


def test_gemini_builds_argv_with_model(monkeypatch):
    monkeypatch.delenv("GEMINI_CMD", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    seen = {}

    def fake_run_cli(cmd, prompt, timeout=180):
        seen["cmd"], seen["prompt"] = cmd, prompt
        return '{"ok": true}'

    monkeypatch.setattr("app.providers.gemini_cli.run_cli", fake_run_cli)
    out = GeminiCLIProvider(model="gemini-2.5-flash").generate("PROMPT")
    assert seen["cmd"] == ["gemini", "-m", "gemini-2.5-flash"]
    assert seen["prompt"] == "PROMPT"
    assert out == '{"ok": true}'


def test_gemini_builds_argv_without_model(monkeypatch):
    monkeypatch.delenv("GEMINI_CMD", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    seen = {}
    monkeypatch.setattr("app.providers.gemini_cli.run_cli",
                        lambda cmd, prompt, timeout=180: seen.update(cmd=cmd) or "{}")
    GeminiCLIProvider().generate("PROMPT")
    assert seen["cmd"] == ["gemini"]


def test_ollama_builds_run_argv(monkeypatch):
    monkeypatch.delenv("OLLAMA_CMD", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    seen = {}
    monkeypatch.setattr("app.providers.ollama.run_cli",
                        lambda cmd, prompt, timeout=300: seen.update(cmd=cmd, prompt=prompt) or "{}")
    OllamaProvider(model="qwen2.5").generate("PROMPT")
    assert seen["cmd"] == ["ollama", "run", "qwen2.5"]
    assert seen["prompt"] == "PROMPT"


def test_ollama_defaults_to_llama(monkeypatch):
    monkeypatch.delenv("OLLAMA_CMD", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    seen = {}
    monkeypatch.setattr("app.providers.ollama.run_cli",
                        lambda cmd, prompt, timeout=300: seen.update(cmd=cmd) or "{}")
    OllamaProvider().generate("PROMPT")
    assert seen["cmd"] == ["ollama", "run", "llama3.1"]


def test_availability_reflects_cli_presence(monkeypatch):
    monkeypatch.setattr("app.providers.gemini_cli.cli_exists", lambda _b: True)
    assert GeminiCLIProvider().is_available() is True
    monkeypatch.setattr("app.providers.gemini_cli.cli_exists", lambda _b: False)
    assert GeminiCLIProvider().is_available() is False


def test_mock_is_always_available():
    assert MockProvider().is_available() is True


def test_mock_returns_schema_valid_json(sample_jd, sample_resume):
    raw = MockProvider().generate(build_prompt(sample_jd, sample_resume, ""))
    docs = parse_docs(raw)  # would raise if not schema-valid
    assert docs.resume.contact.name == "Rashmi Mahadevaiah"
    assert docs.resume.contact.email == "rashmi@example.com"
    assert docs.resume.skills  # picked up Python/PyTorch/AWS etc.
