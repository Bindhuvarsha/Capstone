"""
MigrateIQ Ask API Endpoint
Provides RAG-powered migration Q&A with strict grounding and citations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.agent.state import AgentState
from app.agent.graph import agent_workflow

router = APIRouter(prefix="/ask", tags=["Ask Assistant"])

class AskRequest(BaseModel):
    query: str = Field(..., description="Migration question (e.g. 'What replaces BSEG in S/4HANA?')")

class Citation(BaseModel):
    title: str
    source: str
    topic: str
    release: str
    score: float

class AskResponse(BaseModel):
    query: str
    guardrail_passed: bool
    guardrail_message: Optional[str] = None
    answer: str
    citations: List[Citation] = []
    retrieval_confidence: float

@router.post("", response_model=AskResponse)
def ask_question(request: AskRequest):
    initial_state = AgentState(user_query=request.query)
    final_state = agent_workflow.run(initial_state)

    citations = [
        Citation(
            title=c["title"],
            source=c["source"],
            topic=c["topic"],
            release=c["release"],
            score=c.get("score", 0.0)
        )
        for c in final_state.citations
    ]

    return AskResponse(
        query=request.query,
        guardrail_passed=final_state.guardrail_passed,
        guardrail_message=final_state.guardrail_message if not final_state.guardrail_passed else None,
        answer=final_state.response,
        citations=citations,
        retrieval_confidence=final_state.retrieval_confidence
    )
