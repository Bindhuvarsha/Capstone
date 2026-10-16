"""
MigrateIQ LangGraph Agent Nodes
Planner, Retriever, Scanner tool, Scorer, and Responder nodes.
"""

import os
import requests
from typing import Dict, Any, List
from app.agent.state import AgentState
from app.core.guardrails import guardrails
from app.ingestion.vector_store import VectorStore
from app.ingestion.reranker import SemanticReranker
from app.scanner.engine import ABAPScanner
from app.scanner.scorer import calculate_metrics

vector_store = VectorStore()
reranker = SemanticReranker()
scanner = ABAPScanner()

def planner_node(state: AgentState) -> AgentState:
    """Classifies user intent and validates domain guardrails."""
    # 1. Guardrail Check
    allowed, message, meta = guardrails.validate_query(state.user_query or state.abap_code or "Scan ABAP")
    if not allowed:
        state.guardrail_passed = False
        state.guardrail_message = message
        state.response = f"⚠️ **Guardrail Notice**: {message}"
        return state

    # 2. Intent Classification
    if state.abap_code and len(state.abap_code.strip()) > 0:
        state.query_type = "CODE_SCAN"
    else:
        q_lower = state.user_query.lower()
        if any(w in q_lower for w in ["effort", "risk score", "estimation", "plan", "hours", "timeline", "benchmark"]):
            state.query_type = "PLANNING"
        else:
            state.query_type = "TECHNICAL_QA"

    return state

def retriever_node(state: AgentState) -> AgentState:
    """Fetches candidate chunks and reranks them to eliminate noise."""
    if not state.guardrail_passed:
        return state

    search_query = state.user_query
    if state.query_type == "CODE_SCAN" and state.scan_results:
        # Search documentation relevant to the detected rules
        rule_areas = [f.get("area", "") for f in state.scan_results.get("findings", [])]
        search_query = " ".join(set(rule_areas)) or "SAP S/4HANA custom code migration"

    candidates = vector_store.search(search_query, top_k=6)
    reranked = reranker.rerank(search_query, candidates, top_k=3)

    state.retrieved_docs = reranked
    state.citations = []

    for doc in reranked:
        meta = doc.get("metadata", {})
        state.citations.append({
            "title": meta.get("title", "SAP Reference"),
            "source": meta.get("source", "SAP Simplification List"),
            "topic": meta.get("topic", "Custom Code"),
            "release": meta.get("release", "S/4HANA"),
            "score": doc.get("rerank_score", 0.0)
        })

    if reranked:
        state.retrieval_confidence = max(d.get("rerank_score", 0.0) for d in reranked)
    else:
        state.retrieval_confidence = 0.0

    return state

def scanner_node(state: AgentState) -> AgentState:
    """Executes rule-based scanner over ABAP code."""
    if not state.guardrail_passed or not state.abap_code:
        return state

    scan_out = scanner.scan_code(state.abap_code, state.filename)
    state.scan_results = scan_out
    return state

def scorer_node(state: AgentState) -> AgentState:
    """Calculates risk score and effort estimates per MigrateIQ specification."""
    if not state.guardrail_passed or not state.scan_results:
        return state

    metrics = calculate_metrics(
        state.scan_results.get("findings", []),
        state.scan_results.get("lines_of_code", 1)
    )
    state.metrics = metrics
    return state

def responder_node(state: AgentState) -> AgentState:
    """Generates grounded answer citing sources, or reports weak retrieval."""
    if not state.guardrail_passed:
        return state

    # Check if Groq or Gemini LLM is available
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if state.query_type == "TECHNICAL_QA":
        if state.retrieval_confidence < 0.15 or not state.retrieved_docs:
            state.response = (
                "**MigrateIQ Assistant**: I could not find verified information in the official "
                "SAP S/4HANA documentation for your question. To ensure migration safety, "
                "answers are strictly grounded in verified SAP simplification items."
            )
            return state

        # If LLM key exists, use it with ground context
        if groq_key and groq_key != "your_groq_api_key_here":
            llm_answer = _call_groq_llm(state.user_query, state.retrieved_docs)
            if llm_answer:
                state.response = llm_answer
                return state

        # High-quality deterministic grounded answer synthesis
        context_parts = []
        for i, doc in enumerate(state.retrieved_docs, start=1):
            meta = doc.get("metadata", {})
            context_parts.append(
                f"### Finding from {meta.get('title')} ({meta.get('source')})\n"
                f"{doc.get('text')}\n"
            )

        citations_md = "\n\n**Sources & Citations:**\n" + "\n".join([
            f"- **{c['title']}** | *Source*: {c['source']} | *Topic*: {c['topic']} | *Release*: {c['release']}"
            for c in state.citations
        ])

        state.response = (
            f"Based on the official SAP S/4HANA Simplification Documentation:\n\n"
            f"{''.join(context_parts)}"
            f"{citations_md}"
        )

    elif state.query_type in ("CODE_SCAN", "PLANNING"):
        scan = state.scan_results or {}
        met = state.metrics or {}
        findings = scan.get("findings", [])
        
        md = [
            f"## ABAP Code Analysis Report: `{state.filename}`\n",
            f"- **Lines of Code (LOC)**: {met.get('lines_of_code', 0)}",
            f"- **Total S/4HANA Issues**: {met.get('total_findings', 0)}",
            f"- **Migration Risk Score**: **{met.get('risk_score', 0)} / 1000 LOC** (Rating: `{met.get('risk_rating', 'CLEAN')}`)",
            f"- **Estimated Remediation Effort**: **{met.get('total_effort_hours', 0)} hours** (~{met.get('estimated_person_days', 0)} person-days)\n",
            "### Severity Breakdown:",
            f"- **High Severity**: {met.get('severity_counts', {}).get('high', 0)} issues (4.0 hrs/finding)",
            f"- **Medium Severity**: {met.get('severity_counts', {}).get('medium', 0)} issues (2.0 hrs/finding)",
            f"- **Low Severity**: {met.get('severity_counts', {}).get('low', 0)} issues (0.5 hrs/finding)\n",
            "### Incompatibility Findings:"
        ]

        if not findings:
            md.append("✅ No S/4HANA compatibility issues found in the uploaded code.")
        else:
            for i, f in enumerate(findings, start=1):
                md.append(
                    f"**{i}. [{f['rule_id']}] {f['rule_name']}** (Severity: `{f['severity'].upper()}`)\n"
                    f"- **Line {f['line']}**: `{f['snippet']}`\n"
                    f"- **Issue**: {f['message']}\n"
                    f"- **Recommendation**: {f['recommendation']}\n"
                    f"- **Reference**: {f['source']}\n"
                )

        state.response = "\n".join(md)

    return state

def _call_groq_llm(query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
    """Calls Groq API (Llama 3.3 70B) with strict grounding prompt."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        context_str = "\n\n".join([f"--- Doc: {d.get('metadata', {}).get('title')} ---\n{d.get('text')}" for d in retrieved_docs])
        prompt = (
            "You are MigrateIQ, an expert SAP S/4HANA migration AI consultant. "
            "Answer the user query ONLY using the provided retrieved context. "
            "Always cite the source document. If the answer is not in the context, explicitly say "
            "'I could not find this information in the official documentation.'\n\n"
            f"Retrieved Documentation Context:\n{context_str}\n\n"
            f"User Question: {query}\n\nAnswer with citations:"
        )

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            },
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return ""
