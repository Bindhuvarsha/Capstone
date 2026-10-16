"""
MigrateIQ SQLAlchemy Database Models
Stores Scan Sessions, Individual Findings, and Consultant Approve/Reject Decisions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    filename = Column(String(255), default="uploaded_code.abap")
    total_files = Column(Integer, default=1)
    lines_of_code = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)
    risk_rating = Column(String(32), default="CLEAN")
    effort_hours = Column(Float, default=0.0)
    status = Column(String(32), default="COMPLETED")

    findings = relationship("FindingRecord", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "session_uuid": self.session_uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filename": self.filename,
            "lines_of_code": self.lines_of_code,
            "total_findings": self.total_findings,
            "risk_score": self.risk_score,
            "risk_rating": self.risk_rating,
            "effort_hours": self.effort_hours,
            "status": self.status
        }


class FindingRecord(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("scan_sessions.id", ondelete="CASCADE"), index=True)
    file = Column(String(255), nullable=False)
    line = Column(Integer, nullable=False)
    rule_id = Column(String(32), nullable=False)
    rule_name = Column(String(255), nullable=True)
    area = Column(String(128), default="General")
    severity = Column(String(32), nullable=False)
    snippet = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    explanation = Column(Text, nullable=True)

    session = relationship("ScanSession", back_populates="findings")
    decision = relationship("DecisionRecord", back_populates="finding", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "file": self.file,
            "line": self.line,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "area": self.area,
            "severity": self.severity,
            "snippet": self.snippet,
            "message": self.message,
            "recommendation": self.recommendation,
            "source": self.source,
            "explanation": self.explanation,
            "decision": self.decision.to_dict() if self.decision else {
                "decision": "PENDING",
                "consultant_name": None,
                "notes": None
            }
        }


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), unique=True, index=True)
    decision = Column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED
    consultant_name = Column(String(128), default="SAP Consultant")
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    finding = relationship("FindingRecord", back_populates="decision")

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "decision": self.decision,
            "consultant_name": self.consultant_name,
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
