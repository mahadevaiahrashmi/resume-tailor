# Test Plan — Resume Tailor

## Strategy

Tests run **fully offline** using the deterministic **mock** provider, so the
suite needs no model, no network, and no API keys. Real engines (Claude, Gemini,
Ollama) are validated by **mocking `run_cli`** and asserting the exact command argv and
stdin — we verify *how* we'd call them without actually invoking them.

Run:

```bash
./.venv/bin/python -m pytest
```

Current status: **61 tests passing.**

## Coverage map

| File | Layer | What it verifies |
| --- | --- | --- |
| `tests/test_schema.py` | Domain | Model defaults; `with_contact_fallback` signs the cover letter only when empty. |
| `tests/test_generator.py` | Domain | `extract_json` (plain, fenced, prose-wrapped, brace-in-string, no-object); `parse_docs` (valid, invalid JSON, schema mismatch, **repairs trailing commas + curly quotes**); `generate_documents` (empty inputs, mock success, unavailable-engine hint, provider-error wrapping, **retries once on bad JSON then succeeds**, **gives up after one retry**). |
| `tests/test_providers.py` | Adapters | Registry (`get_provider` default/model/unknown, `list_providers` shape); Claude argv with/without model; Gemini argv with/without model; Ollama `run` argv + default model; availability reflects `cli_exists`; mock always available and schema-valid. **OpenRouter:** availability reflects `OPENROUTER_API_KEY`, request shape (bearer header, model, messages) via a stubbed `httpx.post`, default model, `ProviderError` on missing key / non-200. **Model lists:** `list_providers(include_models=True)` shape, default omits models, Ollama prefers installed models else falls back. |
| `tests/test_render.py` | Adapters | Resume & cover PDFs start with `%PDF` and are **exactly one page**; a near-budget "dense" resume still fits one page (auto-fit); DOCX files reload and contain name, headings, skills, bullets; cover-letter signature fallback. |
| `tests/test_api.py` | Web | `/` renders the form; `/providers` lists mock as available; `/generate` returns 4 files + preview; downloads return correct `Content-Type` + `attachment`; empty JD → 400; non-hex job → 404; path-traversal → 404. **TTL cleanup:** `cleanup_generated` removes only old 32-hex job dirs (leaves fresh + non-job dirs), is disabled at `ttl<=0`, and `/generate` sweeps stale dirs. |

## Key assertions

- **One-page guarantee (PDF).** `_pdf_page_count` counts `/Type /Page` objects in
  the output bytes and asserts `== 1`, including for the dense fixture that
  forces the auto-fit loop to shrink type.
- **Honesty contract is structural.** The schema + `parse_docs` path is tested so
  malformed or partial model output fails loudly rather than producing junk.
- **Command construction.** Claude → `["claude", "-p", "--output-format", "text", "--tools", ""]`
  (+ `["--model", <model>]`); Gemini → `["gemini", "-m", <model>]` (or `["gemini"]`);
  Ollama → `["ollama", "run", <model>]`; prompt always passed on stdin.
- **OpenRouter request shape.** POST to the OpenAI-compatible endpoint with an
  `Authorization: Bearer` header and a `{model, messages:[{role:"user"}]}` body;
  the API key comes from the env and never appears in argv or logs.
- **Model dropdown source.** `/providers` carries each engine's
  `suggested_models()`; the UI builds the per-engine dropdown from it, and Ollama
  surfaces the user's actually-installed models.
- **Download safety.** Job id must be 32-hex; resolved path must stay within
  `generated/`; otherwise 404.

## Test data

Fixtures live in `tests/conftest.py`:
- `sample_jd`, `sample_resume` — realistic inputs used across generator/provider/API tests.
- `docs` — a fully-populated `TailoredDocs` for renderer/API tests.
- `dense_docs` — 5 roles × 3 bullets near the one-page budget, to exercise PDF auto-fit.

The `client` fixture monkeypatches `app.main.GEN` to a pytest `tmp_path`, so test
runs don't litter the real `generated/` directory.

## Manual / exploratory checklist

Automated tests cover logic and contracts; do these by hand when changing UI or
engines:

- [ ] Submit with **Mock** → 4 downloads open and render correctly.
- [ ] Submit with **Claude CLI** (if installed) → genuine rewrite, one page.
- [ ] Submit with **Ollama** (if installed) → output is a genuine rewrite, one page.
- [ ] Submit with **Gemini CLI** (if installed) → same.
- [ ] Open each `.docx` in Word/Google Docs → opens cleanly, is one page.
- [ ] Open each `.pdf` → one page, dates right-aligned, headings ruled.
- [ ] Pick an uninstalled engine → inline hint; submit → readable 400.
- [ ] Resize browser below 860px → layout collapses to one column.
- [ ] Paste resume text containing `<script>` → preview shows it as literal text.

## Known gaps / future tests

- No test asserts DOCX **page count** (python-docx can't measure layout) — see
  [TECH_DEBT.md](TECH_DEBT.md).
- No end-to-end test against a *real* local model (intentionally — keeps CI
  offline and deterministic).
- No load/concurrency tests (v1 is single-user).
- No coverage threshold gate / CI workflow yet.
