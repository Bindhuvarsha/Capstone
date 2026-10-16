"""
MigrateIQ - Modern Streamlit Dashboard
Interactive UI supporting Ask (RAG Assistant), Scan (ABAP Code Analysis),
Plan (Risk & Effort Modeling), and Human Decisions (Approve/Reject flow).
"""

import streamlit as st
import pandas as pd
import requests
import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scanner.engine import ABAPScanner
from app.scanner.scorer import calculate_metrics, SEVERITY_WEIGHTS, EFFORT_HOURS
from app.agent.graph import agent_workflow
from app.agent.state import AgentState
from app.core.database import SessionLocal, init_db
from app.core.models import ScanSession, FindingRecord, DecisionRecord

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MigrateIQ | AI Co-pilot for ECC to S/4HANA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db()

# Custom Modern CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge-high {
        background-color: #FEE2E2;
        color: #DC2626;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #DCFCE7;
        color: #16A34A;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .citation-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin-top: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/59/SAP_2011_logo.svg", width=120)
    st.markdown("### **MigrateIQ Navigator**")
    st.markdown("**AI Co-pilot for SAP ECC to S/4HANA Migration**")
    st.markdown("---")
    
    app_mode = st.radio(
        "Navigation",
        ["💬 Ask MigrateIQ (RAG)", "🔍 ABAP Code Scanner", "📊 Migration Planner & Decisions", "📚 Knowledge Base & Architecture"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("**Target Architecture:**")
    st.caption("• ERP: SAP S/4HANA (Universal Journal ACDOCA)")
    st.caption("• DB: SAP HANA In-Memory Column Store")
    st.caption("• Core: LangGraph + FlashRank Rerank")
    st.caption("• Results DB: SQLite / SQLAlchemy")
    st.markdown("---")
    st.caption("SAP Code Unnati Capstone | October 2026")


# ==============================================================================
# TAB 1: ASK MIGRATEIQ (RAG ASSISTANT)
# ==============================================================================
if app_mode == "💬 Ask MigrateIQ (RAG)":
    st.markdown('<div class="main-header">💬 Ask MigrateIQ: Migration Advisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Query SAP simplification items, data model shifts, and custom code adaptation rules with grounded citations.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Sample prompt selector
        sample_questions = [
            "Select a starter migration question...",
            "What replaces BSEG and secondary index tables in S/4HANA?",
            "How has the Sales Document Status model changed from VBUK/VBUP?",
            "What happened to MKPF and MSEG in S/4HANA material management?",
            "Why is hardcoding MATNR length 18 characters incompatible with S/4HANA?",
            "What is the Business Partner approach and how does it affect KNA1 and LFA1?",
            "How do I bake a chocolate cake? (Test Guardrail Out-of-Scope)"
        ]
        selected_sample = st.selectbox("Quick Questions:", sample_questions)

        default_input = "" if selected_sample.startswith("Select") else selected_sample
        user_query = st.text_area("Your Migration Question:", value=default_input, height=90, placeholder="e.g., How does ACDOCA unify FI and CO line items?")

        ask_button = st.button("🚀 Ask Assistant", type="primary")

        if ask_button and user_query.strip():
            with st.spinner("Evaluating guardrails and retrieving verified SAP documentation..."):
                state = AgentState(user_query=user_query)
                result_state = agent_workflow.run(state)

                if not result_state.guardrail_passed:
                    st.error(result_state.response)
                else:
                    st.success("✅ Information grounded in verified SAP simplification documentation.")
                    st.markdown(result_state.response)

                    if result_state.citations:
                        st.markdown("### 📑 Verified Source Citations")
                        for cit in result_state.citations:
                            st.markdown(f"""
                            <div class="citation-box">
                                <b>{cit['title']}</b><br>
                                <small>📌 <b>Source:</b> {cit['source']} | 🏷️ <b>Topic:</b> {cit['topic']} | 🔄 <b>Release:</b> {cit['release']} | 🎯 <b>Relevance:</b> {cit['score']}</small>
                            </div>
                            """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🛡️ Guardrails & Safety")
        st.info("""
        **Strict Scope Enforcement:**
        - Allowed: SAP S/4HANA, ECC, ABAP, Simplification Items, HANA DB, Fiori, CVI, ACDOCA, MATDOC.
        - Blocked: Out-of-scope non-SAP domains (cooking, movies, general trivia).
        - Protected: Prompt injections & system override attempts.
        - Weak Retrieval Policy: If official documentation is missing, the agent explicitly discloses it cannot verify the answer.
        """)


# ==============================================================================
# TAB 2: ABAP CODE SCANNER
# ==============================================================================
elif app_mode == "🔍 ABAP Code Scanner":
    st.markdown('<div class="main-header">🔍 ABAP Custom Code Migration Scanner</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload or paste custom ABAP programs to detect S/4HANA syntax incompatibilities, obsolete tables, and design shifts.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Input Code")
        sample_options = {
            "Select sample code...": "",
            "FI Report with BSEG, BSIS & Native SQL (High Risk)": "tests/samples/z_fi_report_bad.abap",
            "SD Status & Pricing Report (VBUK, VBUP, KONV)": "tests/samples/z_sd_order_bad.abap",
            "MM Inventory & Master Data (MSEG, MATNR 18, KNA1)": "tests/samples/z_mm_goods_bad.abap",
            "Clean S/4HANA Report (ACDOCA & MATDOC)": "tests/samples/z_clean_code.abap"
        }
        selected_file_sample = st.selectbox("Load sample ABAP program:", list(sample_options.keys()))

        code_to_scan = ""
        sample_path = sample_options[selected_file_sample]
        if sample_path and os.path.exists(sample_path):
            with open(sample_path, "r") as f:
                code_to_scan = f.read()

        uploaded_file = st.file_uploader("Or upload an ABAP file (.abap, .txt):", type=["abap", "txt"])
        if uploaded_file is not None:
            code_to_scan = uploaded_file.read().decode("utf-8", errors="ignore")

        program_name = st.text_input("Program Name:", value="Z_CUSTOM_REPORT.abap")
        abap_input = st.text_area("ABAP Source Code:", value=code_to_scan, height=320)

        scan_btn = st.button("⚡ Run S/4HANA Readiness Scan", type="primary")

    with col2:
        st.markdown("#### Scan Findings & Metrics")
        if scan_btn and abap_input.strip():
            with st.spinner("Parsing AST & evaluating 10 verified S/4HANA rules..."):
                scanner = ABAPScanner()
                scan_res = scanner.scan_code(abap_input, filename=program_name)
                findings = scan_res["findings"]
                loc = scan_res["lines_of_code"]
                metrics = calculate_metrics(findings, loc)

                # Persist to database
                db = SessionLocal()
                import uuid
                session_rec = ScanSession(
                    session_uuid=str(uuid.uuid4()),
                    filename=program_name,
                    lines_of_code=loc,
                    total_findings=len(findings),
                    risk_score=metrics["risk_score"],
                    risk_rating=metrics["risk_rating"],
                    effort_hours=metrics["total_effort_hours"]
                )
                db.add(session_rec)
                db.commit()
                db.refresh(session_rec)

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

                    dec_rec = DecisionRecord(
                        finding_id=f_rec.id,
                        decision="PENDING",
                        consultant_name="SAP Consultant"
                    )
                    db.add(dec_rec)
                    db.commit()
                db.close()

                # Metric Cards
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Lines of Code", loc)
                m_col2.metric("Total Findings", len(findings))
                m_col3.metric("Risk Score", f"{metrics['risk_score']}", delta=metrics['risk_rating'], delta_color="inverse")
                m_col4.metric("Remediation Effort", f"{metrics['total_effort_hours']} hrs")

                st.markdown("---")
                if not findings:
                    st.success("🎉 Code is 100% S/4HANA compliant! No obsolete constructs or table direct access found.")
                else:
                    for i, f in enumerate(findings, start=1):
                        sev = f["severity"].lower()
                        badge_cls = f"badge-{sev}"
                        with st.expander(f"#{i} [{f['rule_id']}] {f['rule_name']} (Line {f['line']})", expanded=True):
                            st.markdown(f'<span class="{badge_cls}">{sev.upper()} SEVERITY</span> | 📂 <b>Area:</b> {f["area"]}', unsafe_allow_html=True)
                            st.code(f"{f['snippet']}", language="sql")
                            st.markdown(f"**Issue:** {f['message']}")
                            st.markdown(f"**Recommendation:** `{f['recommendation']}`")
                            st.caption(f"Reference: {f['source']}")
        else:
            st.info("Paste or select ABAP code on the left and click **Run S/4HANA Readiness Scan**.")


# ==============================================================================
# TAB 3: MIGRATION PLANNER & DECISIONS
# ==============================================================================
elif app_mode == "📊 Migration Planner & Decisions":
    st.markdown('<div class="main-header">📊 Migration Planner & Decision Board</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Review risk scores, effort estimates, and approve or reject AI suggestions with audit notes.</div>', unsafe_allow_html=True)

    db = SessionLocal()
    sessions = db.query(ScanSession).order_by(ScanSession.created_at.desc()).all()

    if not sessions:
        st.warning("No scan sessions recorded yet. Please run a scan in the **ABAP Code Scanner** tab first.")
        db.close()
    else:
        session_dict = {f"Session #{s.id} - {s.filename} ({s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else ''})": s.id for s in sessions}
        selected_session_label = st.selectbox("Select Scan Session to Review:", list(session_dict.keys()))
        selected_session_id = session_dict[selected_session_label]

        current_session = db.query(ScanSession).filter(ScanSession.id == selected_session_id).first()
        findings = db.query(FindingRecord).filter(FindingRecord.session_id == selected_session_id).all()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Program", current_session.filename)
        col2.metric("Risk Score", f"{current_session.risk_score}", delta=current_session.risk_rating, delta_color="inverse")
        col3.metric("Remediation Effort", f"{current_session.effort_hours} hrs")
        col4.metric("Estimated Days", f"{round(current_session.effort_hours / 8.0, 1)} days")

        st.markdown("---")
        st.markdown("### 📋 Findings & Human Approval Workflow")

        for f in findings:
            dec = db.query(DecisionRecord).filter(DecisionRecord.finding_id == f.id).first()
            current_decision = dec.decision if dec else "PENDING"
            consultant = dec.consultant_name if dec else "SAP Consultant"
            notes = dec.notes if dec and dec.notes else ""

            status_color = "gray"
            if current_decision == "APPROVED":
                status_color = "green"
            elif current_decision == "REJECTED":
                status_color = "red"

            with st.container():
                f_col1, f_col2 = st.columns([3, 2])
                with f_col1:
                    st.markdown(f"#### [{f.rule_id}] {f.rule_name} (Line {f.line})")
                    st.code(f.snippet, language="sql")
                    st.markdown(f"**Issue:** {f.message}")
                    st.markdown(f"**Recommendation:** `{f.recommendation}`")

                with f_col2:
                    st.markdown(f"**Decision Status:** :{status_color}[**{current_decision}**]")
                    new_dec = st.radio(f"Action for Finding #{f.id}:", ["PENDING", "APPROVED", "REJECTED"], 
                                       index=["PENDING", "APPROVED", "REJECTED"].index(current_decision),
                                       key=f"dec_radio_{f.id}", horizontal=True)
                    new_notes = st.text_input(f"Remediation Notes / Justification:", value=notes, key=f"notes_{f.id}")
                    
                    if st.button(f"Save Decision #{f.id}", key=f"btn_save_{f.id}"):
                        if not dec:
                            dec = DecisionRecord(finding_id=f.id, decision=new_dec, notes=new_notes)
                            db.add(dec)
                        else:
                            dec.decision = new_dec
                            dec.notes = new_notes
                        db.commit()
                        st.success(f"Decision for #{f.id} updated to {new_dec}!")
                        st.rerun()

                st.markdown("---")

        # Export Report
        st.markdown("### 📤 Export Migration Report")
        report_data = {
            "Program": current_session.filename,
            "Lines of Code": current_session.lines_of_code,
            "Risk Score": current_session.risk_score,
            "Risk Rating": current_session.risk_rating,
            "Effort Hours": current_session.effort_hours,
            "Findings": [
                {
                    "Line": f.line,
                    "Rule": f.rule_id,
                    "Name": f.rule_name,
                    "Severity": f.severity,
                    "Recommendation": f.recommendation,
                    "Decision": f.decision.decision if f.decision else "PENDING",
                    "Notes": f.decision.notes if f.decision else ""
                }
                for f in findings
            ]
        }
        st.download_button(
            label="📥 Download JSON Migration Assessment",
            data=json.dumps(report_data, indent=2),
            file_name=f"migrateiq_assessment_{current_session.filename}.json",
            mime="application/json"
        )
        db.close()


# ==============================================================================
# TAB 4: KNOWLEDGE BASE & ARCHITECTURE
# ==============================================================================
elif app_mode == "📚 Knowledge Base & Architecture":
    st.markdown('<div class="main-header">📚 Knowledge Base & System Architecture</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect ingested SAP simplification items, vector chunks, and architecture blueprints.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🏛️ MigrateIQ Architecture Blueprint")
        st.code("""
User (Streamlit UI)
  │
  ▼
FastAPI Backend ──► NeMo Guardrails (SAP Migration Topic Scope)
  │
  ▼
LangGraph Agent
  ├── Planner Node: Identifies Technical Q&A vs ABAP Scan vs Planning
  ├── Retriever Node: Vector Search + Semantic Rerank (Filters Noise)
  ├── Scanner Tool Node: Runs 10 verified S/4HANA rules over custom code
  ├── Scorer Node: Risk formula: sum(weights * count) / LOC * 1000
  └── Responder Node: Grounded answers with exact citations
  │
  ▼
Results DB (SQLite / PostgreSQL) ◄──► Human Approve/Reject Flow
        """, language="text")

    with col2:
        st.markdown("### 📖 Ingested Knowledge Base")
        from app.ingestion.vector_store import VectorStore
        store = VectorStore()
        st.metric("Total Indexed Chunks", store.count())

        if os.path.exists("DATA"):
            files = [f for f in os.listdir("DATA") if f.endswith(".md")]
            st.markdown("**Indexed Documents in `DATA/`:**")
            for f in files:
                st.markdown(f"- 📄 `{f}`")

        st.info("""
        **RAG Formula & Risk Weights:**
        - High Severity Weight: `5.0` (4.0 remediation hours)
        - Medium Severity Weight: `3.0` (2.0 remediation hours)
        - Low Severity Weight: `1.0` (0.5 remediation hours)
        """)
