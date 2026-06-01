# User Manual — Resume Tailor (technical)

Complete setup and reference for running Resume Tailor locally. For a plain,
non-technical walkthrough see [USER_GUIDE_NONTECH.md](USER_GUIDE_NONTECH.md).

## 1. Requirements

- **Python 3.12** (3.13 also fine; **not 3.14** — pydantic-core has no wheel yet).
- macOS, Linux, or Windows (WSL recommended on Windows).
- Optional engines: **Gemini CLI** and/or **Ollama** (the app also ships a mock
  engine that needs nothing).

## 2. Install & run

```bash
cd resume-tailor
./run.sh
```

`run.sh` creates `.venv`, installs `requirements.txt`, and starts uvicorn on
`http://127.0.0.1:8000`. Override host/port:

```bash
HOST=0.0.0.0 PORT=9000 ./run.sh   # only expose beyond localhost deliberately
```

Manual equivalent:

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --port 8000
```

## 3. Setting up engines

### Gemini CLI
```bash
npm install -g @google/gemini-cli
gemini          # run once to authenticate
```
The app detects `gemini` on your PATH and marks it ✓ detected.

### Ollama (open source)
```bash
# install from https://ollama.com
ollama pull llama3.1     # or: ollama pull qwen2.5
```

### Mock
Always available. It reshapes your resume into the layout without a model — use
it to preview formatting. It does **not** truly rewrite your text.

## 4. Using the app

1. **AI engine** — pick an engine. The form auto-selects the first detected one.
2. **Model (optional)** — override the default model, e.g. `qwen2.5` or
   `gemini-2.5-flash`. Leave blank to use the engine default.
3. **Job description \*** — paste the full posting.
4. **Your current resume \*** — paste your existing resume as plain text.
5. **Extra instructions** — optional, e.g. "Emphasize production ML and
   leadership. Keep a confident tone."
6. Click **Generate documents**. Watch the status banner.
7. On success, use the four **Download** buttons and review the **Preview**
   (Resume / Cover letter tabs).

## 5. Outputs

Four files per run, written to `generated/<job>/`:

- `<Name>_Resume.pdf`
- `<Name>_Resume.docx`
- `<Name>_CoverLetter.pdf`
- `<Name>_CoverLetter.docx`

PDFs are auto-fit to a single A4 page. Word files use compact typography to
match; if your resume is unusually long, trim a bullet or two for best fit.

## 6. Configuration reference

| Variable | Default | Effect |
| --- | --- | --- |
| `GEMINI_CMD` | `gemini` | Gemini CLI binary name/path |
| `GEMINI_MODEL` | (unset) | Model passed to Gemini via `-m` |
| `OLLAMA_CMD` | `ollama` | Ollama binary name/path |
| `OLLAMA_MODEL` | `llama3.1` | Default Ollama model |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Server bind (via `run.sh`) |

A per-run **model** box in the UI overrides `*_MODEL` for that request.

## 7. HTTP endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | The form UI |
| GET | `/providers` | JSON: `[{name, label, available}]` |
| POST | `/generate` | Form fields `jd, resume, instructions, provider, model`; returns `{job, files, preview}` |
| GET | `/download/{job}/{filename}` | Serve a generated file |

## 8. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Engine shows "— not detected" | The CLI isn't on PATH. Install it (§3) and reload. |
| "Gemini CLI not found …" on submit | Same; or set `GEMINI_CMD` to the binary's path. |
| Ollama first run is slow | The model is loading into memory; subsequent runs are faster. |
| 400 "Job description is empty" | Fill both required fields. |
| 400 "Model returned invalid JSON" | The local model didn't follow the JSON contract; retry, or try a stronger model. |
| `pip install` fails on pydantic-core | You're on Python 3.14. Recreate `.venv` with 3.12. |
| Output spills to 2 pages (Word) | DOCX has no auto-fit; trim a bullet (see [TECH_DEBT.md](TECH_DEBT.md)). |

## 9. Testing

```bash
./.venv/bin/python -m pytest
```

Runs fully offline using the mock engine. See [TEST_PLAN.md](TEST_PLAN.md).

## 10. FAQ

**Is my data sent anywhere?** Only to the **local** engine you choose. Mock uses
no network. This app has no telemetry and no third-party calls of its own.

**Does it invent experience?** No. The prompt forbids fabricating employers,
dates, degrees, metrics, or skills; it only reframes what your resume contains.

**Can I edit the result?** Yes — open the `.docx` in Word/Google Docs and edit
freely.
