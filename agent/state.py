"""Shared state passed between LangGraph nodes."""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

# v1 is scoped to these four case types rather than open-ended free text
# classification — see agent/case_types.py for the per-type Jev criteria
# and synthetic sample disputes.
CaseType = Literal[
    "item_not_received",
    "item_damaged",
    "item_not_as_described",
    "refund_not_received",
]


class DisputeState(TypedDict, total=False):
    # Input
    case_type: CaseType
    dispute_text: str  # raw customer complaint / transaction narrative

    # Filled in by the `adjudicate` node (via Jev)
    verdict: Optional[Literal["refund", "deny", "escalate"]]
    verdict_confidence: Optional[float]
    verdict_probabilities: Optional[dict[str, float]]
    severity_score: Optional[float]
    severity_confidence: Optional[float]

    # Filled in by the routing / terminal nodes
    status: Optional[Literal["auto_resolved", "needs_human_review"]]
    notes: Optional[str]
