# Resume Tailor

Paste a job description and your current resume, pick an AI engine, and get a
**tailored, one-page resume and matching cover letter** as both **Word (.docx)**
and **PDF**. Run it through a **local** engine (Ollama or the offline mock) so
nothing leaves your machine, or a **hosted** engine (Claude CLI, Gemini CLI, or
OpenRouter) when you want higher quality.

> Honesty first: the tool reframes and re-emphasises what is already in your
> resume to fit the target job. It is instructed never to invent employers,
> dates, degrees, metrics, or skills.

---

## Features

- **Five engines, one interface**
  - **Claude CLI** — Anthropic's `claude` CLI (highest quality if you have it).
  - **Gemini CLI** — Google's `gemini` CLI.
  - **Ollama** — fully open-source, runs models like `llama3.1` locally.
  - **OpenRouter** — hosted access to DeepSeek, Qwen, Llama, and many more via
    one API key (`OPENROUTER_API_KEY`). Billable per OpenRouter's pricing.
  - **Mock** — offline, no model required; reshapes your resume so you can
    preview the layout instantly. Always available.
- **Per-engine model picker.** The model dropdown updates to the selected engine
  (Ollama lists your installed models); pick **Custom…** to type any model id.
- **Guaranteed one page.** The PDF renderer auto-shrinks typography until both
  documents fit a single A4 page.
- **Four downloads per run:** resume PDF, resume Word, cover letter PDF, cover
  letter Word.
- **Live preview** of the resume and cover letter before you download.
- **Local or hosted, your call.** Ollama and the mock keep your text on your
  machine; the hosted engines send it to their vendor (Anthropic, Google, or
  OpenRouter). This app adds no telemetry and stores no API keys.

## Quickstart

Requires **Python 3.12** (pydantic-core has no wheels for 3.14 yet).

```bash
cd resume-tailor
./run.sh                 # creates .venv, installs deps, starts the server
# open http://127.0.0.1:8000
```

Or manually:

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --port 8000
```

## Choosing an engine

| Engine | Install | Notes |
| --- | --- | --- |
| **Claude CLI** | `npm install -g @anthropic-ai/claude-code`, then run `claude` once to sign in | Optional model `sonnet`/`opus` via the model dropdown or `CLAUDE_MODEL` |
| **Gemini CLI** | `npm install -g @google/gemini-cli`, then run `gemini` once to sign in | Set model via the model dropdown or `GEMINI_MODEL` |
| **Ollama** | Install from [ollama.com](https://ollama.com), then `ollama pull llama3.1` | Default model `llama3.1`; override via the dropdown or `OLLAMA_MODEL` |
| **OpenRouter** | Create a key at [openrouter.ai/keys](https://openrouter.ai/keys), then `export OPENROUTER_API_KEY=sk-or-...` before starting | Hosted/paid; default model `deepseek/deepseek-chat`; pick another from the dropdown or set `OPENROUTER_MODEL` |
| **Mock** | Nothing | Offline preview only; does not truly rewrite text |

The dropdown shows which engines are detected on your machine, and the form
auto-selects the first available one.

## How it works

```
Job description + Resume + Instructions
        │
        ▼
   build_prompt()  ──►  Provider (Claude / Gemini / Ollama / OpenRouter / Mock)  ──►  raw JSON
        │
        ▼
   parse_docs()  →  validated TailoredDocs (pydantic)
        │
        ├──►  render_pdf   →  *.pdf   (auto-fit to 1 page)
        └──►  render_docx  →  *.docx
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) for detail.

## Project layout

```
resume-tailor/
├── app/
│   ├── main.py            FastAPI routes (form, /generate, /download)
│   ├── generator.py       prompt → provider → validated TailoredDocs
│   ├── prompts.py         the tailoring prompt + JSON contract
│   ├── schema.py          pydantic models (the LLM output contract)
│   ├── render_pdf.py      reportlab → 1-page PDF (auto-fit)
│   ├── render_docx.py     python-docx → Word
│   ├── providers/         claude_cli, gemini_cli, ollama, openrouter, mock + registry
│   ├── templates/         index.html
│   └── static/            style.css, app.js
├── tests/                 pytest suite (54 tests)
├── docs/                  product, architecture, user, test docs
├── requirements.txt
└── run.sh
```

## Testing

```bash
./.venv/bin/python -m pytest
```

The suite runs fully offline using the mock provider. See
[docs/TEST_PLAN.md](docs/TEST_PLAN.md).

## Documentation

| Doc | For |
| --- | --- |
| [PRD.md](docs/PRD.md) | Product requirements |
| [PRODUCT_DESIGN.md](docs/PRODUCT_DESIGN.md) | UX and design decisions |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components and structure |
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Request lifecycle, data, security |
| [USER_MANUAL.md](docs/USER_MANUAL.md) | Full setup & reference (technical) |
| [USER_GUIDE_NONTECH.md](docs/USER_GUIDE_NONTECH.md) | Plain-language walkthrough |
| [USER_FLOW.md](docs/USER_FLOW.md) | Journey and states |
| [TEST_PLAN.md](docs/TEST_PLAN.md) | Test strategy and coverage |
| [TECH_DEBT.md](docs/TECH_DEBT.md) | Known limitations and follow-ups |

## Privacy

Where your text goes depends on the engine you pick. **Ollama** and the **mock**
engine run on your machine and send nothing over the network. The **hosted**
engines send your inputs to their vendor's API by design — Claude CLI to
Anthropic, Gemini CLI to Google, and **OpenRouter** to OpenRouter (using a key
you set via `OPENROUTER_API_KEY`, which the app reads from the environment and
never stores). The app adds no telemetry of its own. Generated files are written
to `resume-tailor/generated/` (git-ignored) and served back to your browser.
