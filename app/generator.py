"""Orchestration: inputs -> prompt -> provider -> validated TailoredDocs.

Models don't always return clean JSON, so `extract_json` is defensive: it strips
code fences and isolates the first balanced JSON object before parsing.
"""
from __future__ import annotations

import json

from pydantic import ValidationError

from .prompts import build_prompt
from .providers import ProviderError, get_provider
from .schema import TailoredDocs


class GenerationError(RuntimeError):
    """Raised when the model output can't be turned into valid TailoredDocs."""


def extract_json(raw: str) -> str:
    """Isolate the first balanced JSON object in `raw`.

    Handles ```json fences and leading/trailing prose by scanning for the first
    '{' and counting brace depth (ignoring braces inside strings).
    """
    text = raw.strip()
    if text.startswith("```"):
        # Drop the opening fence line (``` or ```json) and any closing fence.
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    start = text.find("{")
    if start == -1:
        raise GenerationError("No JSON object found in model output.")

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise GenerationError("Unbalanced JSON braces in model output.")


def parse_docs(raw: str) -> TailoredDocs:
    snippet = extract_json(raw)
    try:
        # strict=False tolerates literal newlines/tabs inside string values,
        # which local models (e.g. via Ollama) routinely emit unescaped.
        data = json.loads(snippet, strict=False)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"Model returned invalid JSON: {exc}") from exc
    try:
        docs = TailoredDocs.model_validate(data)
    except ValidationError as exc:
        raise GenerationError(f"Model JSON did not match the schema: {exc}") from exc
    return docs.with_contact_fallback()


def generate_documents(
    jd: str,
    resume: str,
    instructions: str = "",
    provider_name: str = "mock",
    model: str | None = None,
) -> TailoredDocs:
    if not jd.strip():
        raise GenerationError("Job description is empty.")
    if not resume.strip():
        raise GenerationError("Resume is empty.")

    provider = get_provider(provider_name, model)
    if not provider.is_available():
        raise GenerationError(provider.setup_hint() or f"Provider '{provider_name}' is unavailable.")

    prompt = build_prompt(jd, resume, instructions)
    try:
        raw = provider.generate(prompt)
    except ProviderError as exc:
        raise GenerationError(str(exc)) from exc
    return parse_docs(raw)
