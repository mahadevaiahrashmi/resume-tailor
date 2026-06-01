"""FastAPI web app: form in, four tailored documents out.

Routes:
  GET  /                 the input form
  GET  /providers        provider availability (JSON)
  POST /generate         run the pipeline, render 4 files, return links + preview
  GET  /download/{job}/{filename}   serve a generated file
"""
from __future__ import annotations

import os
import re
import shutil
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .generator import GenerationError, generate_documents
from .providers import list_providers
from .render_docx import render_cover_letter_docx, render_resume_docx
from .render_pdf import (
    cover_letter_fit_scale,
    render_cover_letter_pdf,
    render_resume_pdf,
    resume_fit_scale,
)

BASE = Path(__file__).resolve().parent
GEN = BASE.parent / "generated"
GEN.mkdir(exist_ok=True)

# Generated output accumulates one dir per run; sweep dirs older than this on each
# request. Set GENERATED_TTL_HOURS=0 to disable cleanup and keep everything.
GENERATED_TTL_HOURS = float(os.environ.get("GENERATED_TTL_HOURS", "24"))

JOB_RE = re.compile(r"[0-9a-f]{32}")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def cleanup_generated(root: Path, ttl_hours: float) -> int:
    """Delete job dirs older than `ttl_hours`; return how many were removed.

    Only touches 32-hex dirs we created, never anything else dropped in
    `generated/`. A non-positive TTL disables cleanup.
    """
    if ttl_hours <= 0 or not root.exists():
        return 0
    cutoff = time.time() - ttl_hours * 3600
    removed = 0
    for child in root.iterdir():
        if not (child.is_dir() and JOB_RE.fullmatch(child.name)):
            continue
        try:
            if child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                removed += 1
        except OSError:
            pass
    return removed

app = FastAPI(title="Resume Tailor")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))


def safe_slug(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name or "").strip("_")
    return slug[:40] or "candidate"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"providers": list_providers()}
    )


@app.get("/providers")
def providers():
    return list_providers(include_models=True)


@app.post("/generate")
def generate(
    jd: str = Form(...),
    resume: str = Form(...),
    instructions: str = Form(""),
    provider: str = Form("mock"),
    model: str = Form(""),
):
    cleanup_generated(GEN, GENERATED_TTL_HOURS)
    try:
        docs = generate_documents(jd, resume, instructions, provider, model or None)
    except GenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    job = uuid.uuid4().hex
    job_dir = GEN / job
    job_dir.mkdir(parents=True, exist_ok=True)
    slug = safe_slug(docs.resume.contact.name)

    names = {
        "resume_pdf": f"{slug}_Resume.pdf",
        "resume_docx": f"{slug}_Resume.docx",
        "cover_pdf": f"{slug}_CoverLetter.pdf",
        "cover_docx": f"{slug}_CoverLetter.docx",
    }
    # Solve the one-page fit once on the PDF, then render both formats at that
    # scale so the Word file matches the PDF instead of spilling to a 2nd page.
    resume_scale = resume_fit_scale(docs.resume)
    cover_scale = cover_letter_fit_scale(docs.cover_letter, docs.resume.contact)
    render_resume_pdf(docs.resume, str(job_dir / names["resume_pdf"]), scale=resume_scale)
    render_resume_docx(docs.resume, str(job_dir / names["resume_docx"]), scale=resume_scale)
    render_cover_letter_pdf(docs.cover_letter, docs.resume.contact, str(job_dir / names["cover_pdf"]), scale=cover_scale)
    render_cover_letter_docx(docs.cover_letter, docs.resume.contact, str(job_dir / names["cover_docx"]), scale=cover_scale)

    def url(key):
        return f"/download/{job}/{names[key]}"

    return {
        "job": job,
        "files": [
            {"label": "Resume — PDF", "url": url("resume_pdf")},
            {"label": "Resume — Word", "url": url("resume_docx")},
            {"label": "Cover Letter — PDF", "url": url("cover_pdf")},
            {"label": "Cover Letter — Word", "url": url("cover_docx")},
        ],
        "preview": docs.model_dump(),
    }


@app.get("/download/{job}/{filename}")
def download(job: str, filename: str):
    if not JOB_RE.fullmatch(job):
        raise HTTPException(status_code=404, detail="Not found")
    path = (GEN / job / filename).resolve()
    if not str(path).startswith(str(GEN.resolve()) + "/") or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    media = DOCX_MIME if filename.endswith(".docx") else "application/pdf"
    return FileResponse(str(path), media_type=media, filename=filename)
