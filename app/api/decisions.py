"""
MigrateIQ Human-in-the-Loop Decisions API
Stores approve / reject actions and consultant notes in the Results DB.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.core.models import FindingRecord, DecisionRecord, ScanSession

router = APIRouter(prefix="/decisions", tags=["Decisions"])

class DecisionUpdate(BaseModel):
    finding_id: int
    decision: str = Field(..., description="APPROVED, REJECTED, or PENDING")
    consultant_name: Optional[str] = "SAP Consultant"
    notes: Optional[str] = ""

class BulkDecisionUpdate(BaseModel):
    decisions: List[DecisionUpdate]

@router.post("")
def update_decision(payload: DecisionUpdate, db: Session = Depends(get_db)):
    """Sets human approval or rejection on a specific finding."""
    norm_decision = payload.decision.upper().strip()
    if norm_decision not in ("APPROVED", "REJECTED", "PENDING"):
        raise HTTPException(status_code=400, detail="Decision must be APPROVED, REJECTED, or PENDING")

    finding = db.query(FindingRecord).filter(FindingRecord.id == payload.finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    decision_rec = db.query(DecisionRecord).filter(DecisionRecord.finding_id == payload.finding_id).first()
    if not decision_rec:
        decision_rec = DecisionRecord(
            finding_id=payload.finding_id,
            decision=norm_decision,
            consultant_name=payload.consultant_name,
            notes=payload.notes,
            updated_at=datetime.utcnow()
        )
        db.add(decision_rec)
    else:
        decision_rec.decision = norm_decision
        decision_rec.consultant_name = payload.consultant_name or decision_rec.consultant_name
        decision_rec.notes = payload.notes
        decision_rec.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(decision_rec)
    return decision_rec.to_dict()

@router.post("/bulk")
def update_bulk_decisions(payload: BulkDecisionUpdate, db: Session = Depends(get_db)):
    """Applies bulk decision updates across findings."""
    updated = []
    for item in payload.decisions:
        rec = update_decision(item, db)
        updated.append(rec)
    return {"updated_count": len(updated), "decisions": updated}

@router.get("/session/{session_id}")
def get_session_decisions(session_id: int, db: Session = Depends(get_db)):
    """Retrieves all findings and their decisions for a specific scan session."""
    session_rec = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session_rec:
        raise HTTPException(status_code=404, detail="Scan session not found")

    findings = db.query(FindingRecord).filter(FindingRecord.session_id == session_id).all()
    results = [f.to_dict() for f in findings]

    approved_count = sum(1 for f in results if f["decision"]["decision"] == "APPROVED")
    rejected_count = sum(1 for f in results if f["decision"]["decision"] == "REJECTED")
    pending_count = sum(1 for f in results if f["decision"]["decision"] == "PENDING")

    return {
        "session": session_rec.to_dict(),
        "summary": {
            "total_findings": len(findings),
            "approved": approved_count,
            "rejected": rejected_count,
            "pending": pending_count
        },
        "findings": results
    }
