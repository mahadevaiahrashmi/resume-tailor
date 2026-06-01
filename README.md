# Resume Tailor

Paste a job description and your current resume, pick an AI engine, and get a
**tailored, one-page resume and matching cover letter** as both **Word (.docx)**
and **PDF**. Generation runs **locally** through a CLI engine you choose — nothing
is uploaded to a third-party server by this app.

> Honesty first: the tool reframes and re-emphasises what is already in your
> resume to fit the target job. It is instructed never to invent employers,
> dates, degrees, metrics, or skills.

---

## Features

- **Three engines, one interface**
  - **Gemini CLI** — Google's `gemini` CLI (best quality if you have it).
  - **Ollama** — fully open-source, runs models like `llama3.1` locally.
  - **Mock** — offline, no model required; reshapes your resume so you can
    preview the layout instantly. Always available.
- **Guaranteed one page.** The PDF renderer auto-shrinks typography until both
  documents fit a single A4 page.
- **Four downloads per run:** resume PDF, resume Word, cover letter PDF, cover
  letter Word.
- **Live preview** of the resume and cover letter before you download.
- **Local & private.** The web app calls a local CLI; your text is not sent to
  this project's servers.

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
| **Gemini CLI** | `npm install -g @google/gemini-cli`, then run `gemini` once to sign in | Set model with the optional model box or `GEMINI_MODEL` |
| **Ollama** | Install from [ollama.com](https://ollama.com), then `ollama pull llama3.1` | Default model `llama3.1`; override per-run or with `OLLAMA_MODEL` |
| **Mock** | Nothing | Offline preview only; does not truly rewrite text |

The dropdown shows which engines are detected on your machine, and the form
auto-selects the first available one.

## How it works

```
Job description + Resume + Instructions
        │
        ▼
   build_prompt()  ──►  Provider (Gemini / Ollama / Mock)  ──►  raw JSON
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
│   ├── providers/         gemini_cli, ollama, mock + registry
│   ├── templates/         index.html
│   └── static/            style.css, app.js
├── tests/                 pytest suite (40 tests)
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

Your resume and the job description are sent only to the **local** engine you
select. The mock engine touches no network at all. Generated files are written
to `resume-tailor/generated/` (git-ignored) and served back to your browser.
