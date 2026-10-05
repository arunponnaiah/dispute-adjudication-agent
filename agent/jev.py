"""Thin wrapper around TypeSafe's Jev (System One) decision model.

Jev takes a piece of state plus a set of typed questions and returns typed,
calibrated answers instead of free text. Here we ask it two questions about
a dispute: a `choice` (what the verdict should be) and a `score` (how severe
the dispute is), and hand the typed, probability-scored answers back to the
LangGraph nodes.

Docs: https://docs.typesafe.ai
"""

from __future__ import annotations

import os

from langfuse import get_client as get_langfuse_client
from typesafe_sdk import Choice, Score, TypeSafeClient

from agent.case_types import CASE_TYPES
from agent.state import CaseType

_client: TypeSafeClient | None = None


def get_jev_client() -> TypeSafeClient:
    global _client
    if _client is None:
        # Reads TYPESAFE_API_KEY from the environment if api_key is omitted.
        _client = TypeSafeClient(api_key=os.environ.get("TYPESAFE_API_KEY"))
    return _client


def adjudicate_dispute(dispute_text: str, case_type: CaseType) -> dict:
    """Ask Jev for a verdict and a severity score on a dispute narrative.

    `case_type` selects the case-type-specific verdict criteria from
    agent/case_types.py (e.g. what matters for "item not received" differs
    from what matters for "item not as described").

    Returns a plain dict so callers don't need to import typesafe_sdk types:
        {
            "verdict": "refund" | "deny" | "escalate",
            "verdict_confidence": float,
            "verdict_probabilities": {"refund": .., "deny": .., "escalate": ..},
            "severity_score": float,
            "severity_confidence": float,
        }
    """
    client = get_jev_client()
    state = {"case_type": case_type, "dispute_text": dispute_text}
    questions = {
        "verdict": Choice(
            instructions=CASE_TYPES[case_type]["verdict_instructions"],
            criteria={
                "refund": "The merchant was clearly at fault; refund the customer.",
                "deny": "The claim is not valid and the dispute should be denied.",
                "escalate": (
                    "The evidence is mixed, insufficient, or high-stakes; "
                    "a human adjudicator should review it."
                ),
            },
        ),
        "severity": Score(
            instructions="Rate how severe/urgent this dispute is.",
            criteria=[
                "Low severity: minor issue, low dollar amount, easy to resolve.",
                "Medium severity: moderate dollar amount, or some ambiguity "
                "/ customer effort already spent chasing a resolution.",
                "High severity: large dollar amount, repeated seller "
                "non-responsiveness, or signs of bad-faith conduct.",
            ],
        ),
    }

    # Jev isn't a LangChain-wrapped LLM, so LangGraph's Langfuse callback
    # handler can't see this call automatically. Instrument it manually as
    # a `generation` observation so model name / token usage / cost show up
    # in Langfuse like any other LLM call, nested under whichever LangGraph
    # node (span) is currently active.
    with get_langfuse_client().start_as_current_observation(
        name="jev-adjudicate",
        as_type="generation",
        model="jev-latest",  # default alias; corrected below from the response
        input={"state": state, "questions": list(questions.keys())},
    ) as generation:
        response = client.system_one(state=state, questions=questions)

        verdict_answer = response.answers["verdict"]
        severity_answer = response.answers["severity"]

        result = {
            "verdict": verdict_answer.choice,
            "verdict_confidence": verdict_answer.confidence,
            "verdict_probabilities": verdict_answer.probabilities,
            "severity_score": severity_answer.score,
            "severity_confidence": severity_answer.confidence,
        }

        usage_details = {
            key: value
            for key, value in (
                ("input_tokens", response.usage.input_tokens),
                ("output_tokens", response.usage.output_tokens),
            )
            if value is not None
        }
        generation.update(
            model=response.model,
            output=result,
            usage_details=usage_details or None,
        )

    return result
