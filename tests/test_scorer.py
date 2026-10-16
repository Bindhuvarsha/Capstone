"""
MigrateIQ Risk & Effort Scorer Test Suite
Verifies mathematical correctness of formulas specified in Section 9.3.
"""

import pytest
from app.scanner.scorer import calculate_metrics, SEVERITY_WEIGHTS, EFFORT_HOURS

def test_risk_formula_calculation():
    # 2 high findings (5*2=10), 1 medium (3*1=3), 1 low (1*1=1) = total 14 points
    # LOC = 100
    # Expected risk = (14 / 100) * 1000 = 140.0
    findings = [
        {"severity": "high"},
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"}
    ]
    loc = 100
    metrics = calculate_metrics(findings, loc)

    assert metrics["risk_score"] == 140.0
    assert metrics["risk_rating"] == "CRITICAL"
    assert metrics["severity_counts"]["high"] == 2
    assert metrics["severity_counts"]["medium"] == 1
    assert metrics["severity_counts"]["low"] == 1

def test_effort_hours_calculation():
    # 1 high (4h), 2 medium (2*2 = 4h), 2 low (2*0.5 = 1h) = total 9 hours
    findings = [
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "medium"},
        {"severity": "low"},
        {"severity": "low"}
    ]
    metrics = calculate_metrics(findings, 200)

    assert metrics["total_effort_hours"] == 9.0
    assert metrics["estimated_person_days"] == round(9.0 / 8.0, 2)
    assert metrics["effort_breakdown"]["high_hours"] == 4.0
    assert metrics["effort_breakdown"]["medium_hours"] == 4.0
    assert metrics["effort_breakdown"]["low_hours"] == 1.0

def test_zero_findings_clean_score():
    metrics = calculate_metrics([], 500)
    assert metrics["risk_score"] == 0.0
    assert metrics["risk_rating"] == "CLEAN"
    assert metrics["total_effort_hours"] == 0.0

def test_zero_loc_safety():
    metrics = calculate_metrics([{"severity": "high"}], 0)
    assert metrics["risk_score"] == 0.0
