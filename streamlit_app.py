"""Streamlit UI for the dispute adjudication agent.

Usage:
    source .venv/bin/activate
    streamlit run streamlit_app.py
"""

from __future__ import annotations

from dotenv import load_dotenv

# Load .env before importing anything from `agent` — Langfuse (imported by
# agent.runner) reads its credentials from the environment the first time
# its client is constructed.
load_dotenv()

import streamlit as st  # noqa: E402

from agent.case_types import CASE_TYPES  # noqa: E402
from agent.runner import run_dispute  # noqa: E402

st.set_page_config(page_title="Dispute Adjudication Agent", page_icon="⚖️")
st.title("⚖️ Dispute Adjudication Agent")
st.caption("LangGraph orchestration · Jev (TypeSafe) as the decision model")

case_type = st.selectbox(
    "Case type",
    options=list(CASE_TYPES.keys()),
    format_func=lambda key: CASE_TYPES[key]["label"],
)

dispute_text = st.text_area(
    "Dispute narrative",
    value=CASE_TYPES[case_type]["sample_dispute"],
    height=180,
    key=f"dispute_text_{case_type}",  # reset the textarea when case type changes
)

if st.button("Adjudicate", type="primary"):
    with st.spinner("Asking Jev..."):
        result = run_dispute(dispute_text, case_type, channel="streamlit")

    status = result.get("status")
    verdict = result.get("verdict")

    if status == "auto_resolved":
        st.success(f"Auto-resolved: **{verdict}**")
    else:
        st.warning(f"Needs human review (leaning: **{verdict}**)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Verdict", verdict or "—")
    col2.metric("Confidence", f"{(result.get('verdict_confidence') or 0):.0%}")
    col3.metric("Severity", f"{(result.get('severity_score') or 0):.2f}")

    st.subheader("Verdict probabilities")
    st.bar_chart(result.get("verdict_probabilities") or {})

    st.subheader("Notes")
    st.write(result.get("notes"))

    with st.expander("Raw agent state"):
        st.json(result)
