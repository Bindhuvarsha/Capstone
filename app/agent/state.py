"""
MigrateIQ Agent State Definition
Defines the state passed across LangGraph nodes.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    user_query: str = ""
    query_type: str = "TECHNICAL_QA"  # TECHNICAL_QA, CODE_SCAN, PLANNING, GENERAL
    abap_code: Optional[str] = None
    filename: str = "custom_program.abap"
    guardrail_passed: bool = True
    guardrail_message: str = ""
    
    # Retrieval
    retrieved_docs: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_confidence: float = 0.0

    # Scanning & Scoring
    scan_results: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

    # Final Output
    response: str = ""
    session_id: Optional[int] = None
