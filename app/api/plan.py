"""
MigrateIQ Migration Planning API
Delivers aggregated risk scores, effort estimates, and portfolio analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import ScanSession, FindingRecord
from app.scanner.scorer import calculate_metrics

router = APIRouter(prefix="/plan", tags=["Migration Planning"])

@router.get("/portfolio")
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Computes aggregate risk and effort across all scanned programs in the codebase."""
    sessions = db.query(ScanSession).all()
    if not sessions:
        return {
            "total_programs": 0,
            "total_loc": 0,
            "total_findings": 0,
            "aggregate_risk_score": 0.0,
            "aggregate_effort_hours": 0.0,
            "estimated_person_days": 0.0,
            "programs": []
        }

    total_loc = sum(s.lines_of_code for s in sessions)
    total_findings = sum(s.total_findings for s in sessions)
    total_effort = sum(s.effort_hours for s in sessions)

    all_findings_records = db.query(FindingRecord).all()
    all_findings_dicts = [f.to_dict() for f in all_findings_records]

    overall_metrics = calculate_metrics(all_findings_dicts, max(1, total_loc))

    return {
        "total_programs": len(sessions),
        "total_loc": total_loc,
        "total_findings": total_findings,
        "aggregate_risk_score": overall_metrics["risk_score"],
        "aggregate_risk_rating": overall_metrics["risk_rating"],
        "aggregate_effort_hours": overall_metrics["total_effort_hours"],
        "estimated_person_days": overall_metrics["estimated_person_days"],
        "severity_breakdown": overall_metrics["severity_counts"],
        "programs": [s.to_dict() for s in sessions]
    }

@router.get("/{session_id}")
def get_session_plan(session_id: int, db: Session = Depends(get_db)):
    """Fetches detailed plan and remediation breakdown for a single program."""
    session_rec = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session_rec:
        raise HTTPException(status_code=404, detail="Scan session not found")

    findings = db.query(FindingRecord).filter(FindingRecord.session_id == session_id).all()
    findings_dicts = [f.to_dict() for f in findings]
    metrics = calculate_metrics(findings_dicts, session_rec.lines_of_code)

    return {
        "session": session_rec.to_dict(),
        "metrics": metrics,
        "findings_count": len(findings),
        "findings": findings_dicts
    }
