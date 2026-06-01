"""API routes via TestClient, including the download path-traversal guard."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import DOCX_MIME


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Redirect generated output into a temp dir; both /generate and /download
    # read the module-level GEN at call time, so this keeps them consistent.
    monkeypatch.setattr(main, "GEN", tmp_path)
    return TestClient(main.app)


def test_index_renders_form(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Resume Tailor" in r.text
    assert 'name="provider"' in r.text


def test_providers_endpoint_lists_mock(client):
    r = client.get("/providers")
    assert r.status_code == 200
    assert any(p["name"] == "mock" and p["available"] for p in r.json())


def test_generate_returns_four_files_and_preview(client, sample_jd, sample_resume):
    r = client.post("/generate", data={
        "jd": sample_jd, "resume": sample_resume,
        "instructions": "", "provider": "mock", "model": "",
    })
    assert r.status_code == 200, r.text
    payload = r.json()
    assert len(payload["files"]) == 4
    assert payload["preview"]["resume"]["contact"]["name"] == "Rashmi Mahadevaiah"


def test_generated_files_download_with_correct_types(client, sample_jd, sample_resume):
    payload = client.post("/generate", data={
        "jd": sample_jd, "resume": sample_resume, "provider": "mock",
    }).json()
    for f in payload["files"]:
        d = client.get(f["url"])
        assert d.status_code == 200
        assert "attachment" in d.headers.get("content-disposition", "")
        expected = "application/pdf" if f["url"].endswith(".pdf") else DOCX_MIME
        assert d.headers["content-type"] == expected


def test_generate_empty_jd_returns_400(client, sample_resume):
    r = client.post("/generate", data={
        "jd": "", "resume": sample_resume, "provider": "mock",
    })
    assert r.status_code == 400


def test_download_rejects_non_hex_job(client):
    assert client.get("/download/not-a-real-job/x.pdf").status_code == 404


def test_download_rejects_path_traversal(client):
    job = "a" * 32  # well-formed hex job id, but the file escapes the dir
    r = client.get(f"/download/{job}/..%2f..%2fmain.py")
    assert r.status_code == 404
