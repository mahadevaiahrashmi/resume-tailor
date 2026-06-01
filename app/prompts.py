"""Prompt construction for the tailoring step.

A single prompt string is built and handed to whichever provider is selected
(Gemini CLI or Ollama). Both are instructed to return STRICT JSON matching the
schema in `schema.py`. The generator is responsible for parsing/repairing the
response, but a tight prompt keeps that rare.
"""
from __future__ import annotations

# Shown to the model so it knows the exact JSON shape to emit.
JSON_CONTRACT = """{
  "resume": {
    "contact": {
      "name": "Full Name",
      "email": "name@example.com",
      "phone": "+1-555-0100",
      "links": ["linkedin.com/in/handle", "github.com/handle"]
    },
    "summary": "2-3 sentence professional summary, tailored to the job.",
    "skills": [
      {"label": "Languages & ML", "items": "Python, SQL, PyTorch, TensorFlow"},
      {"label": "Cloud & MLOps", "items": "AWS, Docker, Kubernetes"}
    ],
    "experience": [
      {
        "company": "Company",
        "title": "Job Title",
        "dates": "Jan 2025 - Jul 2025",
        "bullets": ["Achievement-oriented bullet with a metric.", "Another bullet."]
      }
    ],
    "education": ["B.Tech, Electrical Engineering - IIT Madras, 2011"]
  },
  "cover_letter": {
    "date": "June 1, 2026",
    "recipient": ["Hiring Manager", "Company Name", "City, Country"],
    "salutation": "Dear Hiring Manager,",
    "paragraphs": ["First paragraph.", "Second paragraph.", "Closing paragraph."],
    "closing": "Sincerely,",
    "signature": "Full Name"
  }
}"""

RULES = """RULES — read carefully:
1. HONESTY: Use ONLY facts present in the candidate's resume. Never invent jobs,
   employers, dates, degrees, metrics, or skills. You may rephrase, reorder, and
   re-emphasise to fit the job, but every claim must trace to the resume.
2. TAILORING: Reframe the resume through the lens of the target job. Mirror the
   job's vocabulary where it honestly applies. Put the most relevant experience
   and skills first. Follow the user's extra instructions exactly.
3. ONE PAGE EACH: Both documents must fit on a single A4 page. Stay within these
   budgets:
   - summary: <= 55 words.
   - skills: <= 5 lines, each a short comma-separated list.
   - experience: keep ALL real roles, but trim bullets. Recent/relevant roles get
     2-4 bullets; older roles get 1-2. Total bullets across all roles <= 16. Each
     bullet <= 32 words, achievement-first, ideally with a metric.
   - education: one line per entry.
   - cover_letter.paragraphs: 3-4 paragraphs, <= 320 words total.
4. OUTPUT: Return ONLY a single JSON object matching the schema below. No prose,
   no markdown, no code fences, no comments. Start with { and end with }."""


def build_prompt(jd: str, resume: str, instructions: str) -> str:
    extra = instructions.strip() or "(none)"
    return f"""You are an expert resume writer and career coach. You tailor a candidate's
existing resume to a specific job and write a matching cover letter, then return
the result as structured JSON for automated formatting.

=== TARGET JOB DESCRIPTION ===
{jd.strip()}

=== CANDIDATE'S CURRENT RESUME ===
{resume.strip()}

=== EXTRA INSTRUCTIONS FROM THE CANDIDATE ===
{extra}

{RULES}

=== JSON SCHEMA (shape to emit; replace the example values) ===
{JSON_CONTRACT}

Now output the tailored JSON object and nothing else."""
