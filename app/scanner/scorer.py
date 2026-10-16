"""
MigrateIQ Risk & Effort Estimation Engine
Implements the exact formulas defined in Section 9.3 of the Capstone guide.
"""

from typing import List, Dict, Any

# Weights calibrated as per MigrateIQ specification Section 9.3
SEVERITY_WEIGHTS = {
    "high": 5.0,
    "medium": 3.0,
    "low": 1.0
}

# Effort estimate in engineering hours per finding
EFFORT_HOURS = {
    "high": 4.0,
    "medium": 2.0,
    "low": 0.5
}

def calculate_metrics(findings: List[Dict[str, Any]], lines_of_code: int) -> Dict[str, Any]:
    """
    Computes risk score and effort estimates based on findings and LOC.
    Formula:
        risk = (sum(severity_weight * count) / lines_of_code) * 1000
    """
    counts = {
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for f in findings:
        sev = f.get("severity", "medium").lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["low"] += 1

    # Total weighted penalty
    total_weighted_points = (
        counts["high"] * SEVERITY_WEIGHTS["high"] +
        counts["medium"] * SEVERITY_WEIGHTS["medium"] +
        counts["low"] * SEVERITY_WEIGHTS["low"]
    )

    # Risk score calculation (normalized per 1,000 LOC)
    if lines_of_code > 0:
        raw_risk = (total_weighted_points / lines_of_code) * 1000.0
        risk_score = round(raw_risk, 2)
    else:
        risk_score = 0.0

    # Risk rating classification
    if risk_score >= 80.0:
        risk_rating = "CRITICAL"
        risk_color = "#E53E3E"
    elif risk_score >= 40.0:
        risk_rating = "HIGH"
        risk_color = "#DD6B20"
    elif risk_score >= 15.0:
        risk_rating = "MEDIUM"
        risk_color = "#D69E2E"
    elif risk_score > 0.0:
        risk_rating = "LOW"
        risk_color = "#38A169"
    else:
        risk_rating = "CLEAN"
        risk_color = "#3182CE"

    # Effort calculation
    effort_by_severity = {
        "high_hours": counts["high"] * EFFORT_HOURS["high"],
        "medium_hours": counts["medium"] * EFFORT_HOURS["medium"],
        "low_hours": counts["low"] * EFFORT_HOURS["low"],
    }
    total_effort_hours = sum(effort_by_severity.values())
    estimated_person_days = round(total_effort_hours / 8.0, 2)

    return {
        "lines_of_code": lines_of_code,
        "total_findings": len(findings),
        "severity_counts": counts,
        "risk_score": risk_score,
        "risk_rating": risk_rating,
        "risk_color": risk_color,
        "total_effort_hours": round(total_effort_hours, 1),
        "estimated_person_days": estimated_person_days,
        "effort_breakdown": effort_by_severity,
        "formula": "risk = sum(severity_weight * count) / lines_of_code * 1000"
    }
