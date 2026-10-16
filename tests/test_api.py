"""
MigrateIQ API End-to-End Test Suite
Tests FastAPI endpoints: health, scan, decisions, plan, and ask.
"""

import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app"] == "MigrateIQ"

def test_scan_endpoint():
    abap_snippet = """
    REPORT z_test.
    SELECT * FROM bseg INTO TABLE lt_bseg.
    """
    resp = client.post("/api/v1/scan", json={"code": abap_snippet, "filename": "z_test.abap"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] is not None
    assert data["total_findings"] >= 1
    assert data["metrics"]["risk_score"] > 0
    assert any(f["rule_id"] == "R001" for f in data["findings"])

def test_decisions_flow():
    # First create a scan
    abap_snippet = "REPORT z_dec. SELECT * FROM vbuk INTO TABLE lt."
    scan_resp = client.post("/api/v1/scan", json={"code": abap_snippet, "filename": "z_dec.abap"})
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    finding_id = scan_data["findings"][0]["id"]
    session_id = scan_data["session_id"]

    # Submit an approve decision
    dec_resp = client.post("/api/v1/decisions", json={
        "finding_id": finding_id,
        "decision": "APPROVED",
        "consultant_name": "Senior SAP Architect",
        "notes": "Refactor to select directly from VBAK."
    })
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["decision"] == "APPROVED"
    assert dec_data["consultant_name"] == "Senior SAP Architect"

    # Verify session decision summary
    sess_resp = client.get(f"/api/v1/decisions/session/{session_id}")
    assert sess_resp.status_code == 200
    sess_data = sess_resp.json()
    assert sess_data["summary"]["approved"] == 1

def test_plan_portfolio_endpoint():
    resp = client.get("/api/v1/plan/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_programs" in data
    assert "aggregate_risk_score" in data
    assert "estimated_person_days" in data

def test_ask_endpoint_in_scope():
    resp = client.post("/api/v1/ask", json={"query": "What replaces BSEG in SAP S/4HANA?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["guardrail_passed"] is True
    assert "answer" in data

def test_ask_endpoint_out_of_scope():
    resp = client.post("/api/v1/ask", json={"query": "How do I bake chocolate cookies?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["guardrail_passed"] is False
    assert "Guardrail Notice" in data["answer"]
