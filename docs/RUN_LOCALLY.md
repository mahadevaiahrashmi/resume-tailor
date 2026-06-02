# Run / Stop Resume Tailor Locally

Quick reference for starting and stopping the app on your own machine. The server
is FastAPI + uvicorn and binds to **`127.0.0.1:8000`** by default (localhost only).

> Requires **Python 3.12** — pydantic-core has no wheels for 3.14 yet.

---

## Start

### Easiest — `run.sh`

```bash
cd /Users/rashmi/Documents/mt/resume-tailor
./run.sh
```

On first run this creates `.venv`, installs `requirements.txt`, then starts the
server. Subsequent runs reuse the venv and start immediately. When it's up you'll
see:

```
Resume Tailor running at http://127.0.0.1:8000
```

Open **http://127.0.0.1:8000** in your browser.

### Manual (if you'd rather not use the script)

```bash
cd /Users/rashmi/Documents/mt/resume-tailor
python3.12 -m venv .venv                       # once
./.venv/bin/pip install -r requirements.txt    # once
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Development mode (auto-reload on code edits)

By default the server does **not** reload when you edit Python. For active
development, add uvicorn's `--reload` (passed straight through by `run.sh`):

```bash
./run.sh --reload
```

---

## Optional configuration (environment variables)

Set these **before** starting the server:

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Bind address (keep localhost unless you know what you're doing — there's no auth). |
| `PORT` | `8000` | Port to serve on. e.g. `PORT=9000 ./run.sh` |
| `GENERATED_TTL_HOURS` | `24` | Auto-delete generated files older than this many hours; `0` disables cleanup. |
| `OPENROUTER_API_KEY` | — | Required only for the OpenRouter engine. `export OPENROUTER_API_KEY=sk-or-...` |
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | Override the OpenRouter model. |
| `CLAUDE_MODEL` / `GEMINI_MODEL` / `OLLAMA_MODEL` | per-engine | Override the model for those CLI engines. |

Example — start on port 9000 with OpenRouter enabled:

```bash
export OPENROUTER_API_KEY=sk-or-...your-key...
PORT=9000 ./run.sh
```

---

## Stop

### If it's running in your terminal (foreground)

Press **`Ctrl + C`** in the window where `run.sh` is running.

### If it's running in the background / you closed the terminal

Find and stop whatever is listening on the port (default 8000):

```bash
# graceful stop
lsof -ti tcp:8000 | xargs kill

# if it won't quit, force it
lsof -ti tcp:8000 | xargs kill -9
```

(Change `8000` if you started it on a different `PORT`.)

---

## Run it in the background on purpose

```bash
cd /Users/rashmi/Documents/mt/resume-tailor
nohup ./run.sh > server.log 2>&1 &
echo "started PID $!"      # note the PID, or use the lsof command above to stop it
tail -f server.log         # watch startup; Ctrl+C just stops tailing, not the server
```

Stop it with the `lsof ... | xargs kill` command above.

---

## Verify it's up

```bash
curl -s http://127.0.0.1:8000/providers
```

You should get a JSON list of engines with their availability. The browser form
at `http://127.0.0.1:8000` should also load.

---

## Sanity-check the code (optional)

Runs fully offline via the mock engine — no model or network needed:

```bash
./.venv/bin/python -m pytest
```

---

## Troubleshooting

- **`Address already in use` / port busy** — something is already on 8000. Stop it
  with `lsof -ti tcp:8000 | xargs kill`, or start on another port: `PORT=9000 ./run.sh`.
- **Wrong Python / pydantic install errors** — make sure the venv is 3.12:
  `./.venv/bin/python --version`. If it's 3.14, delete `.venv` and recreate with
  `python3.12 -m venv .venv`.
- **OpenRouter shows unavailable** — the key isn't in the environment of the
  process that started the server. `export OPENROUTER_API_KEY=...` first, then
  restart.
