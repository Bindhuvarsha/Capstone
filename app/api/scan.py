"""
MigrateIQ Code Scan API Endpoint
Accepts ABAP code, runs rules, calculates risk & effort, and persists results in SQLite.
"""

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.models import ScanSession, FindingRecord, DecisionRecord
from app.scanner.engine import ABAPScanner
from app.scanner.scorer import calculate_metrics

router = APIRouter(prefix="/scan", tags=["Code Scanner"])
scanner = ABAPScanner()

class ScanCodeRequest(BaseModel):
    code: str
    filename: Optional[str] = "custom_program.abap"

@router.post("")
def scan_custom_code(
    request: Optional[ScanCodeRequest] = None,
    db: Session = Depends(get_db)
):
    if not request or not request.code.strip():
        raise HTTPException(status_code=400, detail="No ABAP code provided for scanning.")

    code = request.code
    filename = request.filename or "custom_program.abap"

    # Execute scanner
    scan_result = scanner.scan_code(code, filename=filename)
    findings = scan_result["findings"]
    loc = scan_result["lines_of_code"]

    # Calculate metrics
    metrics = calculate_metrics(findings, loc)

    # Persist in SQLite
    session_uuid = str(uuid.uuid4())
    session_rec = ScanSession(
        session_uuid=session_uuid,
        filename=filename,
        lines_of_code=loc,
        total_findings=len(findings),
        risk_score=metrics["risk_score"],
        risk_rating=metrics["risk_rating"],
        effort_hours=metrics["total_effort_hours"],
        status="COMPLETED"
    )
    db.add(session_rec)
    db.commit()
    db.refresh(session_rec)

    # Persist individual findings and default pending decisions
    persisted_findings = []
    for f in findings:
        f_rec = FindingRecord(
            session_id=session_rec.id,
            file=f["file"],
            line=f["line"],
            rule_id=f["rule_id"],
            rule_name=f["rule_name"],
            area=f["area"],
            severity=f["severity"],
            snippet=f["snippet"],
            message=f["message"],
            recommendation=f["recommendation"],
            source=f["source"]
        )
        db.add(f_rec)
        db.commit()
        db.refresh(f_rec)

        # Initialize pending decision
        dec_rec = DecisionRecord(
            finding_id=f_rec.id,
            decision="PENDING",
            consultant_name="SAP Consultant"
        )
        db.add(dec_rec)
        db.commit()

        persisted_findings.append(f_rec.to_dict())

    return {
        "session_id": session_rec.id,
        "session_uuid": session_uuid,
        "filename": filename,
        "metrics": metrics,
        "total_findings": len(persisted_findings),
        "findings": persisted_findings
    }

@router.post("/upload")
async def upload_abap_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handles multi-part ABAP file upload."""
    content_bytes = await file.read()
    code = content_bytes.decode("utf-8", errors="ignore")
    return scan_custom_code(
        request=ScanCodeRequest(code=code, filename=file.filename),
        db=db
    )

@router.get("/sessions")
def list_scan_sessions(db: Session = Depends(get_db)):
    """Returns all previous scan sessions."""
    sessions = db.query(ScanSession).order_by(ScanSession.created_at.desc()).all()
    return [s.to_dict() for s in sessions]
