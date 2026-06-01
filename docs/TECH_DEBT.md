# Tech Debt & Known Limitations — Resume Tailor

Honest inventory of shortcuts and limitations in v1, with impact and a suggested
fix for each. Nothing here blocks the core use case (local, single-user
tailoring); these matter most if the app is hardened or hosted.

## Legend
**Impact:** 🔴 high · 🟡 medium · 🟢 low

---

### 1. DOCX has no measured one-page fit 🟡
`render_docx` relies on compact typography plus the prompt's length budgets, not
a real layout measurement — python-docx has no layout engine. A very long resume
can spill onto a second Word page even though the PDF (which *is* auto-fit) stays
on one.
**Fix:** convert/measure via LibreOffice headless or a docx→pdf check in CI; or
mirror the PDF's scale decision into font sizing. **Workaround:** trim a bullet.

### 2. `generated/` cleanup 🟡 — ✅ resolved
Every run writes four files under `generated/<job>/`. `cleanup_generated()` now
runs at the start of each `/generate` request, deleting job dirs older than
`GENERATED_TTL_HOURS` (default 24; set `0` to disable). Only the 32-hex dirs the
app created are ever touched, so anything else left in `generated/` is safe.

### 3. Synchronous, blocking generation 🟡
`/generate` calls the CLI provider synchronously inside the request handler.
Fine for one local user; under concurrency it ties up workers for the full model
runtime.
**Fix:** offload to a worker/task queue and return a job id the client polls;
make routes `async` and run CLIs in a thread/process pool.

### 4. No authentication or rate limiting 🔴 (if exposed)
The app is designed for `127.0.0.1`. There is no auth, CSRF protection, or rate
limiting, so it must **not** be exposed to the public internet as-is.
**Fix:** add auth + per-IP rate limiting + CSRF before any networked deployment;
keep it localhost-only otherwise.

### 5. Mock provider is heuristic, not a rewrite 🟢
The mock parses contact/skills/experience with regexes and reshapes text; it
does not truly tailor. It exists for offline preview and tests. Edge cases:
phone/skill detection can be approximate.
**Fix:** none needed — it's intentional. Just don't mistake mock output for a
real tailoring.

### 6. Repair of malformed model JSON 🟡 — ✅ resolved
`extract_json` strips fences/prose and `parse_docs` uses `json.loads(strict=False)`,
so literal newlines/tabs inside string values parse fine. On top of that,
`_repair_json` now makes a tolerant pass (normalise curly quotes, strip trailing
commas) and `generate_documents` **retries once** with a "return JSON only"
reminder before surfacing an error. Still best-effort: severely truncated output
can still 400.

### 7. One fixed layout/theme 🟢
A single visual template is hard-coded across PDF/DOCX/preview.
**Fix:** parameterise styles into selectable themes; keep the three renderers in
sync via a shared style object.

### 8. Resume must be pasted as text 🟢
No upload/parsing of an existing `.pdf`/`.docx` resume.
**Fix:** add an upload route that extracts text (e.g. `pdfminer`,
`python-docx`) and pre-fills the resume box.

### 9. No streaming progress for slow local runs 🟢
Ollama's first run can take ~a minute with only a static "Working…" banner.
**Fix:** stream tokens/heartbeats via SSE/websocket to a progress indicator.

### 10. CI pipeline 🟡 — ✅ resolved
`.github/workflows/ci.yml` runs on every push and pull request: it sets up
Python 3.12, installs `requirements.txt`, and runs `pytest` (fully offline via
the mock engine).

### 11. Pinned to Python 3.12 🟢
pydantic-core lacks 3.14 wheels; the venv must be 3.12/3.13. Documented, but a
sharp edge for newcomers on 3.14.
**Fix:** revisit when pydantic-core ships 3.14 wheels; pin in `pyproject` and
document clearly (done in README/USER_MANUAL).

---

## Summary table

| # | Item | Impact | Effort |
| --- | --- | --- | --- |
| 1 | DOCX no measured fit | 🟡 | M |
| 2 | `generated/` cleanup | ✅ done | S |
| 3 | Blocking generation | 🟡 | M |
| 4 | No auth/rate limit (if hosted) | 🔴 | M |
| 5 | Mock is heuristic | 🟢 | — |
| 6 | JSON repair + retry | ✅ done | S |
| 7 | Single theme | 🟢 | M |
| 8 | Paste-only input | 🟢 | M |
| 9 | No progress streaming | 🟢 | M |
| 10 | CI pipeline | ✅ done | S |
| 11 | Python 3.12 pin | 🟢 | — |

Priorities if hardening for shared/hosted use: **#4 → #3** (#2, #6, #10 now resolved).
