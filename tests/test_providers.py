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
from app.providers.claude_cli import ClaudeCLIProvider
from app.providers.gemini_cli import GeminiCLIProvider
from app.providers.ollama import OllamaProvider
from app.providers.openrouter import OpenRouterProvider


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
    assert {p["name"] for p in provs} == {"claude", "gemini", "ollama", "openrouter", "mock"}
    assert all({"name", "label", "available"} <= set(p) for p in provs)
    mock = next(p for p in provs if p["name"] == "mock")
    assert mock["available"] is True


def test_list_providers_includes_models_when_requested():
    by_name = {p["name"]: p for p in list_providers(include_models=True)}
    assert all(isinstance(p["models"], list) for p in by_name.values())
    assert by_name["claude"]["models"]  # non-empty suggestions
    assert "deepseek/deepseek-chat" in by_name["openrouter"]["models"]
    assert by_name["mock"]["models"] == []


def test_list_providers_omits_models_by_default():
    assert all("models" not in p for p in list_providers())


def test_ollama_suggested_models_prefers_installed(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "installed_models", lambda self: ["mymodel:latest"])
    assert OllamaProvider().suggested_models() == ["mymodel:latest"]


def test_ollama_suggested_models_falls_back_to_static(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "installed_models", lambda self: [])
    assert OllamaProvider().suggested_models() == ["llama3.1", "qwen2.5", "mistral", "gemma2"]


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


def test_claude_builds_argv_with_model(monkeypatch):
    monkeypatch.delenv("CLAUDE_CMD", raising=False)
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    seen = {}

    def fake_run_cli(cmd, prompt, timeout=180):
        seen["cmd"], seen["prompt"] = cmd, prompt
        return '{"ok": true}'

    monkeypatch.setattr("app.providers.claude_cli.run_cli", fake_run_cli)
    out = ClaudeCLIProvider(model="opus").generate("PROMPT")
    assert seen["cmd"] == ["claude", "-p", "--output-format", "text", "--tools", "", "--model", "opus"]
    assert seen["prompt"] == "PROMPT"
    assert out == '{"ok": true}'


def test_claude_builds_argv_without_model(monkeypatch):
    monkeypatch.delenv("CLAUDE_CMD", raising=False)
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    seen = {}
    monkeypatch.setattr("app.providers.claude_cli.run_cli",
                        lambda cmd, prompt, timeout=180: seen.update(cmd=cmd) or "{}")
    ClaudeCLIProvider().generate("PROMPT")
    assert seen["cmd"] == ["claude", "-p", "--output-format", "text", "--tools", ""]


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


class _FakeResp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_openrouter_is_available_reflects_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-xxx")
    assert OpenRouterProvider().is_available() is True
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert OpenRouterProvider().is_available() is False


def test_openrouter_builds_request(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-xxx")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, json=json, timeout=timeout)
        return _FakeResp(payload={"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr("app.providers.openrouter.httpx.post", fake_post)
    out = OpenRouterProvider(model="qwen/qwen-2.5-72b-instruct").generate("PROMPT")
    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer sk-or-xxx"
    assert seen["json"]["model"] == "qwen/qwen-2.5-72b-instruct"
    assert seen["json"]["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert out == '{"ok": true}'


def test_openrouter_defaults_to_deepseek(monkeypatch):
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    assert OpenRouterProvider().model == "deepseek/deepseek-chat"


def test_openrouter_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ProviderError):
        OpenRouterProvider().generate("PROMPT")


def test_openrouter_error_status_raises(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-xxx")
    monkeypatch.setattr(
        "app.providers.openrouter.httpx.post",
        lambda *a, **k: _FakeResp(status_code=401, text="no credit"),
    )
    with pytest.raises(ProviderError):
        OpenRouterProvider().generate("PROMPT")


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
