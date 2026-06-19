"""Tests for the FastAPI endpoints in api.py.

The LLM-backed functions (diagnose, evaluate) are patched so tests are fast,
deterministic, and make no live Groq API calls.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

SAMPLE_WORKFLOW = "I copy leads from emails into a CRM by hand every day."
FAKE_PLAN = "## Workflow Summary\nYou copy leads manually.\n## Recommended First Automation\n..."


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------
def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /diagnose
# ---------------------------------------------------------------------------
def test_diagnose_success():
    with patch.object(main, "diagnose", return_value=FAKE_PLAN) as mock_diag:
        resp = client.post("/diagnose", json={"workflow_description": SAMPLE_WORKFLOW})
    assert resp.status_code == 200
    assert resp.json() == {"plan": FAKE_PLAN}
    mock_diag.assert_called_once_with(SAMPLE_WORKFLOW)


def test_diagnose_empty_string_is_422():
    # pydantic min_length=1 rejects before the handler runs.
    resp = client.post("/diagnose", json={"workflow_description": ""})
    assert resp.status_code == 422


def test_diagnose_missing_field_is_422():
    resp = client.post("/diagnose", json={})
    assert resp.status_code == 422


def test_diagnose_value_error_is_422():
    with patch.object(main, "diagnose", side_effect=ValueError("bad input")):
        resp = client.post("/diagnose", json={"workflow_description": SAMPLE_WORKFLOW})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "bad input"


def test_diagnose_llm_failure_is_502():
    with patch.object(main, "diagnose", side_effect=RuntimeError("groq down")):
        resp = client.post("/diagnose", json={"workflow_description": SAMPLE_WORKFLOW})
    assert resp.status_code == 502
    assert "groq down" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# /evaluate
# ---------------------------------------------------------------------------
def test_evaluate_markdown_default():
    report = "**Overall Score:** 86/100"
    with patch.object(main, "evaluate", return_value=report) as mock_eval:
        resp = client.post(
            "/evaluate",
            json={"workflow_description": SAMPLE_WORKFLOW, "plan": FAKE_PLAN},
        )
    assert resp.status_code == 200
    assert resp.json() == {"report": report}
    mock_eval.assert_called_once_with(SAMPLE_WORKFLOW, FAKE_PLAN, structured=False)


def test_evaluate_structured_returns_dict():
    scores = {"overall_score": 86, "breakdown": []}
    with patch.object(main, "evaluate", return_value=scores) as mock_eval:
        resp = client.post(
            "/evaluate",
            json={
                "workflow_description": SAMPLE_WORKFLOW,
                "plan": FAKE_PLAN,
                "structured": True,
            },
        )
    assert resp.status_code == 200
    assert resp.json() == scores
    mock_eval.assert_called_once_with(SAMPLE_WORKFLOW, FAKE_PLAN, structured=True)


def test_evaluate_missing_plan_is_422():
    resp = client.post("/evaluate", json={"workflow_description": SAMPLE_WORKFLOW})
    assert resp.status_code == 422


def test_evaluate_llm_failure_is_502():
    with patch.object(main, "evaluate", side_effect=RuntimeError("groq down")):
        resp = client.post(
            "/evaluate",
            json={"workflow_description": SAMPLE_WORKFLOW, "plan": FAKE_PLAN},
        )
    assert resp.status_code == 502


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
