"""LangGraph orchestration for the dispute adjudication agent.

Flow:
    intake -> adjudicate (Jev) -> [route on confidence] -> finalize | escalate
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.case_types import CASE_TYPES
from agent.jev import adjudicate_dispute
from agent.state import DisputeState

# Below this confidence, don't trust Jev's verdict on its own — send to a
# human adjudicator instead of auto-resolving.
CONFIDENCE_THRESHOLD = 0.75


def intake(state: DisputeState) -> DisputeState:
    """Normalize/validate the incoming dispute narrative and case type."""
    case_type = state.get("case_type")
    if case_type not in CASE_TYPES:
        raise ValueError(
            f"Unknown case_type {case_type!r}. Supported in this version: "
            f"{', '.join(CASE_TYPES)}."
        )
    text = state["dispute_text"].strip()
    return {"case_type": case_type, "dispute_text": text}


def adjudicate(state: DisputeState) -> DisputeState:
    """Call Jev for a typed verdict + severity score on the dispute."""
    result = adjudicate_dispute(state["dispute_text"], state["case_type"])
    return {
        "verdict": result["verdict"],
        "verdict_confidence": result["verdict_confidence"],
        "verdict_probabilities": result["verdict_probabilities"],
        "severity_score": result["severity_score"],
        "severity_confidence": result["severity_confidence"],
    }


def route_on_confidence(state: DisputeState) -> str:
    """Decide whether Jev's verdict is trustworthy enough to auto-resolve."""
    if (
        state.get("verdict") == "escalate"
        or (state.get("verdict_confidence") or 0) < CONFIDENCE_THRESHOLD
    ):
        return "escalate"
    return "finalize"


def finalize(state: DisputeState) -> DisputeState:
    return {
        "status": "auto_resolved",
        "notes": (
            f"Jev verdict '{state['verdict']}' "
            f"(confidence {state['verdict_confidence']:.2f}) auto-resolved."
        ),
    }


def escalate(state: DisputeState) -> DisputeState:
    return {
        "status": "needs_human_review",
        "notes": (
            f"Jev verdict '{state.get('verdict')}' "
            f"(confidence {state.get('verdict_confidence', 0):.2f}) "
            f"fell below the {CONFIDENCE_THRESHOLD} threshold or was "
            "'escalate' — routed to a human adjudicator."
        ),
    }


def build_graph():
    graph = StateGraph(DisputeState)

    graph.add_node("intake", intake)
    graph.add_node("adjudicate", adjudicate)
    graph.add_node("finalize", finalize)
    graph.add_node("escalate", escalate)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "adjudicate")
    graph.add_conditional_edges(
        "adjudicate",
        route_on_confidence,
        {"finalize": "finalize", "escalate": "escalate"},
    )
    graph.add_edge("finalize", END)
    graph.add_edge("escalate", END)

    return graph.compile()
