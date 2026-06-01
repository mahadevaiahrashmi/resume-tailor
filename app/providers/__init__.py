"""Provider registry and lookup."""
from __future__ import annotations

from .base import LLMProvider, ProviderError
from .gemini_cli import GeminiCLIProvider
from .mock import MockProvider
from .ollama import OllamaProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "gemini": GeminiCLIProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider,
}

_NEEDS_MODEL = {"gemini", "ollama"}


def get_provider(name: str | None, model: str | None = None) -> LLMProvider:
    key = (name or "mock").lower()
    cls = PROVIDERS.get(key)
    if cls is None:
        raise ProviderError(
            f"Unknown provider '{name}'. Choose from {sorted(PROVIDERS)}."
        )
    if key in _NEEDS_MODEL and model:
        return cls(model=model)
    return cls()


def list_providers() -> list[dict]:
    """Provider metadata for the UI: name, label, availability."""
    out = []
    for key, cls in PROVIDERS.items():
        inst = cls()
        out.append({
            "name": key,
            "label": inst.label,
            "available": inst.is_available(),
        })
    return out


__all__ = [
    "LLMProvider",
    "ProviderError",
    "GeminiCLIProvider",
    "OllamaProvider",
    "MockProvider",
    "PROVIDERS",
    "get_provider",
    "list_providers",
]
