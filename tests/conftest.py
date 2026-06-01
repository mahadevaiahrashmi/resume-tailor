"""Shared fixtures: sample inputs and ready-made TailoredDocs for the suite."""
from __future__ import annotations

import pytest

from app.schema import (
    Contact,
    CoverLetter,
    ExperienceItem,
    ResumeContent,
    SkillLine,
    TailoredDocs,
)

SAMPLE_JD = """Senior Machine Learning Engineer at Globex Corporation
We are looking for someone strong in Python, PyTorch, AWS, Docker, and
LLM / RAG systems. You will build production ML pipelines and mentor engineers.
"""

SAMPLE_RESUME = """Rashmi Mahadevaiah
rashmi@example.com | +1-555-0142 | linkedin.com/in/rashmi | github.com/rashmi

Senior Data Scientist - Acme Corp  (Jan 2022 - Present)
- Built a RAG pipeline with PyTorch and AWS SageMaker serving 2M requests/day.
- Led a team of 4 building NL2SQL agents for analytics self-service.
Data Scientist - Initech  (2018 - 2022)
- Shipped NER and sentiment models into production for support routing.
B.Tech, Electrical Engineering - IIT Madras, 2011
"""


@pytest.fixture
def sample_jd() -> str:
    return SAMPLE_JD


@pytest.fixture
def sample_resume() -> str:
    return SAMPLE_RESUME


@pytest.fixture
def docs() -> TailoredDocs:
    """A realistic, fully-populated TailoredDocs for renderer/API tests."""
    return TailoredDocs(
        resume=ResumeContent(
            contact=Contact(
                name="Rashmi Mahadevaiah",
                email="rashmi@example.com",
                phone="+1-555-0142",
                links=["linkedin.com/in/rashmi", "github.com/rashmi"],
            ),
            summary=("Senior ML engineer with production experience in RAG, NLP, "
                     "and cloud MLOps, focused on shipping reliable systems."),
            skills=[
                SkillLine(label="Languages & ML", items="Python, SQL, PyTorch, TensorFlow"),
                SkillLine(label="Cloud & MLOps", items="AWS, Docker, Kubernetes"),
            ],
            experience=[
                ExperienceItem(
                    company="Acme Corp", title="Senior Data Scientist",
                    dates="Jan 2022 - Present",
                    bullets=["Built a RAG pipeline serving 2M requests/day.",
                             "Led a team of four engineers."],
                ),
                ExperienceItem(
                    company="Initech", title="Data Scientist", dates="2018 - 2022",
                    bullets=["Shipped NER and sentiment models into production."],
                ),
            ],
            education=["B.Tech, Electrical Engineering - IIT Madras, 2011"],
        ),
        cover_letter=CoverLetter(
            date="June 1, 2026",
            recipient=["Hiring Manager", "Globex Corporation", "City, Country"],
            salutation="Dear Hiring Manager,",
            paragraphs=[
                "I am writing to apply for the Senior ML Engineer role.",
                "My background in production RAG and NLP maps to your needs.",
                "I would welcome a conversation. Thank you for your consideration.",
            ],
            closing="Sincerely,",
            signature="Rashmi Mahadevaiah",
        ),
    )


@pytest.fixture
def dense_docs() -> TailoredDocs:
    """Near the one-page budget (5 roles, 15 bullets) to exercise PDF auto-fit."""
    experience = [
        ExperienceItem(
            company=f"Company {i}", title="Senior Engineer",
            dates="2020 - 2024",
            bullets=[f"Delivered measurable result number {i}-{j} with a clear metric."
                     for j in range(3)],
        )
        for i in range(5)
    ]
    return TailoredDocs(
        resume=ResumeContent(
            contact=Contact(name="Dense Candidate", email="dense@example.com",
                            phone="+1-555-0000", links=["linkedin.com/in/dense"]),
            summary=("Experienced engineer with a long track record across many "
                     "teams and domains, summarised here within the budget."),
            skills=[SkillLine(label=f"Area {i}", items="Tool A, Tool B, Tool C, Tool D")
                    for i in range(5)],
            experience=experience,
            education=["B.Tech - Example Institute, 2010",
                       "M.S. - Example University, 2014"],
        ),
        cover_letter=CoverLetter(
            paragraphs=["Paragraph one.", "Paragraph two.", "Paragraph three."],
            signature="Dense Candidate",
        ),
    )
