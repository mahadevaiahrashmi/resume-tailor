"""Deterministic offline provider.

Produces schema-valid JSON from the inputs using simple heuristics — no network,
no model. It exists so the app and the test suite run end-to-end without Gemini
or Ollama installed, and so users can preview the formatting before wiring up a
real model. It does NOT truly rewrite the resume; it reshapes what it can parse.
"""
from __future__ import annotations

import datetime as _dt
import re

from ..schema import (
    Contact,
    CoverLetter,
    ExperienceItem,
    ResumeContent,
    SkillLine,
    TailoredDocs,
)
from .base import LLMProvider

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){2,5}\d")
LINK_RE = re.compile(r"((?:linkedin\.com|github\.com|gitlab\.com)/[\w/-]+)", re.I)
YEAR_RANGE_RE = re.compile(r"(19|20)\d{2}.*?(present|current|(19|20)\d{2})", re.I)

SKILL_KEYWORDS = {
    "Languages & ML": [
        "python", "sql", "java", "scala", "c++", "pytorch", "tensorflow",
        "scikit-learn", "sklearn", "keras", "spark mllib", "xgboost",
    ],
    "Generative AI & LLMs": [
        "llm", "rag", "mcp", "agent", "prompt", "nl2sql", "vector", "ocr",
        "transformer", "genai", "generative",
    ],
    "NLP & Vision": [
        "ner", "lda", "topic model", "sentiment", "pos tagging", "n-gram",
        "computer vision", "captioning", "text mining",
    ],
    "Cloud & MLOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "sagemaker", "spark",
        "kafka", "airflow", "mlflow",
    ],
}


def _first_name_line(resume: str) -> str:
    for raw in resume.splitlines():
        line = raw.strip().lstrip("#").strip()
        if line and "@" not in line and not line.lower().startswith(("http", "www")):
            return re.sub(r"[*_`]", "", line)[:60]
    return "Candidate Name"


def _scan_skills(resume: str) -> list[SkillLine]:
    low = resume.lower()
    lines: list[SkillLine] = []
    for label, kws in SKILL_KEYWORDS.items():
        seen, items = set(), []
        for k in kws:
            if k in low:
                disp = k.title()
                if disp.lower() not in seen:
                    seen.add(disp.lower())
                    items.append(disp)
        if items:
            lines.append(SkillLine(label=label, items=", ".join(items[:8])))
    return lines[:5]


_EDU_KEYS = ("b.tech", "btech", "b.e", "b.sc", "m.tech", "m.s", "msc", "bachelor",
             "master", "phd", "university", "institute", "college")


def _scan_experience(resume: str) -> list[ExperienceItem]:
    lines = [ln.rstrip() for ln in resume.splitlines()]
    items: list[ExperienceItem] = []
    current: ExperienceItem | None = None
    for ln in lines:
        s = ln.strip("-* \t")
        if not s:
            continue
        looks_edu = any(k in s.lower() for k in _EDU_KEYS)
        is_header = (bool(YEAR_RANGE_RE.search(s)) or " — " in ln or " – " in ln) and not looks_edu
        if is_header and len(s) < 120:
            current = ExperienceItem(company=s[:80], title="", dates="", bullets=[])
            items.append(current)
        elif current is not None and len(current.bullets) < 3:
            current.bullets.append(s[:200])
    if not items:
        bullets = [ln.strip("-* \t")[:200] for ln in lines if ln.strip()][:5]
        items = [ExperienceItem(company="Experience", title="(from resume)",
                                dates="", bullets=bullets or ["See attached resume."])]
    return items[:6]


def _scan_education(resume: str) -> list[str]:
    out = []
    for ln in resume.splitlines():
        if any(k in ln.lower() for k in _EDU_KEYS):
            out.append(ln.strip("-* \t")[:120])
    return out[:3]


def _between(text: str, start: str, end: str) -> str:
    try:
        a = text.index(start) + len(start)
        b = text.index(end, a)
        return text[a:b].strip()
    except ValueError:
        return text.strip()


def _company_from_jd(jd: str) -> str:
    for ln in jd.splitlines():
        m = re.search(r"\bat\s+([A-Z][\w&.\- ]{2,40})", ln)
        if m:
            return m.group(1).strip()
    return ""


def _today() -> str:
    t = _dt.date.today()
    return f"{t.strftime('%B')} {t.day}, {t.year}"


class MockProvider(LLMProvider):
    name = "mock"
    label = "Mock (offline preview)"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str) -> str:
        jd = _between(prompt, "=== TARGET JOB DESCRIPTION ===",
                      "=== CANDIDATE'S CURRENT RESUME ===")
        resume = _between(prompt, "=== CANDIDATE'S CURRENT RESUME ===",
                          "=== EXTRA INSTRUCTIONS FROM THE CANDIDATE ===")
        job_title = (jd.strip().splitlines() or ["the role"])[0][:80]
        name = _first_name_line(resume)
        email_m = EMAIL_RE.search(resume)
        phone_m = PHONE_RE.search(resume)
        links: list[str] = []
        for m in LINK_RE.finditer(resume):
            if m.group(1) not in links:
                links.append(m.group(1))

        docs = TailoredDocs(
            resume=ResumeContent(
                contact=Contact(
                    name=name,
                    email=email_m.group(0) if email_m else "",
                    phone=phone_m.group(0).strip() if phone_m else "",
                    links=links[:3],
                ),
                summary=(f"Candidate profile reshaped for {job_title}. "
                         "(Offline preview — connect Gemini CLI or Ollama for a true rewrite.)"),
                skills=_scan_skills(resume),
                experience=_scan_experience(resume),
                education=_scan_education(resume),
            ),
            cover_letter=CoverLetter(
                date=_today(),
                recipient=["Hiring Manager", _company_from_jd(jd), ""],
                salutation="Dear Hiring Manager,",
                paragraphs=[
                    f"I am writing to apply for {job_title}. My background maps "
                    "closely to what this role requires.",
                    "My experience spans the responsibilities outlined in the "
                    "posting; the attached resume details the specifics.",
                    "I would welcome the chance to discuss how I can contribute. "
                    "Thank you for your consideration.",
                ],
                closing="Sincerely,",
                signature=name,
            ),
        )
        return docs.model_dump_json()
