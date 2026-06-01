# Product Requirements Document — Resume Tailor

**Status:** v1 shipped · **Owner:** Rashmi Mahadevaiah · **Last updated:** 2026-06-01

## 1. Problem

Tailoring a resume and cover letter to each job is slow, repetitive, and easy to
do dishonestly (padding with skills you don't have). Job seekers want a fast way
to **reframe their real experience** for a specific posting and walk away with
polished, one-page documents in the formats employers expect (Word and PDF) —
without handing their resume to an opaque cloud service.

## 2. Goals

- G1. Turn a job description + an existing resume into a tailored resume **and**
  cover letter in one action.
- G2. Output **one-page** documents in **both .docx and .pdf**.
- G3. Support **local** engines (open-source **Ollama**; offline **Mock**) and
  **hosted** engines (**Claude CLI**, **Gemini CLI**, and **OpenRouter**'s API),
  selectable per run.
- G4. Be **honest by construction** — never fabricate experience; only reframe
  what the resume contains.
- G5. Work **offline for preview** so users can try the layout with no model
  installed.

## 3. Non-goals

- Not an applicant tracking system or job board.
- Not a resume *content* generator from scratch — it tailors an existing resume.
- No account system, cloud storage, or multi-user collaboration in v1.
- No hosted multi-tenant deployment in v1 (local single-user app).

## 4. Personas

- **Primary — "Active applicant" (technical).** Comfortable installing a CLI,
  applying to several roles a week, wants speed and control over their data.
- **Secondary — "Non-technical applicant."** Can follow a short guide, mainly
  wants the mock/Ollama path and clear download buttons. Served by
  [USER_GUIDE_NONTECH.md](USER_GUIDE_NONTECH.md).

## 5. User stories

- As an applicant, I paste a JD and my resume, click one button, and get four
  files to download.
- As an applicant, I can add free-text instructions ("emphasise leadership,
  confident tone") that the engine follows.
- As an applicant, I can pick which AI engine runs, and see which are installed.
- As a privacy-conscious user, I can pick a local engine (Ollama or Mock) so my
  text never leaves my machine.
- As a first-time user with no model, I can still preview the formatting (mock).

## 6. Functional requirements

| ID | Requirement |
| --- | --- |
| FR1 | Accept three inputs: job description (required), resume (required), extra instructions (optional). |
| FR2 | Offer engine selection: Claude CLI, Gemini CLI, Ollama, OpenRouter, Mock; show detection status. |
| FR3 | Offer a per-run model choice via a per-engine dropdown, with a Custom option for any model id (e.g. `sonnet`, `qwen2.5`, `deepseek/deepseek-chat`). |
| FR4 | Produce a tailored resume and cover letter as validated structured data. |
| FR5 | Render each document to one-page **PDF** and **Word**. |
| FR6 | Return four downloadable files and a live HTML preview of both documents. |
| FR7 | Reject empty JD or resume with a clear error. |
| FR8 | Serve generated files safely (no path traversal, scoped to the run). |

## 7. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR1 | **One page:** PDFs must always fit a single A4 page (auto-fit). |
| NFR2 | **Honesty:** the prompt forbids inventing facts; claims must trace to the resume. |
| NFR3 | **Privacy:** local engines (Ollama, Mock) make no network calls. Hosted engines (Claude CLI, Gemini CLI, OpenRouter) send inputs to their vendor by the user's explicit choice; the app stores no API keys and adds no telemetry. |
| NFR4 | **Offline-capable:** mock engine + full test suite run with no model and no network. |
| NFR5 | **Safe rendering:** preview uses DOM text nodes (no HTML injection from model output). |
| NFR6 | **Setup clarity:** unavailable engines show install hints inline. |

## 8. Acceptance criteria

- Submitting a JD + resume with the mock engine returns 4 files and a preview
  containing the candidate's name, summary, skills, experience, and education.
- The generated resume PDF is exactly one page even for a near-budget resume
  (verified in tests: `test_dense_resume_still_one_page`).
- Selecting an uninstalled engine surfaces an install hint rather than a crash.
- Empty JD or resume returns HTTP 400 with a readable message.
- `pytest` passes fully offline.

## 9. Success metrics

- Time from paste → downloaded documents: under ~1 minute on mock; under a few
  minutes on a local model's first run.
- Zero fabricated facts in spot checks of tailored output.
- Both documents one page in 100% of runs.

## 10. Out of scope / future

- Resume *upload* parsing (PDF/DOCX in) instead of paste.
- Multiple page templates / themes.
- Side-by-side diff of original vs. tailored.
- Cleanup/TTL for the `generated/` directory (see [TECH_DEBT.md](TECH_DEBT.md)).
