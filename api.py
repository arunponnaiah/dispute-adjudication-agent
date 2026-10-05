"""FastAPI service exposing the dispute adjudication agent.

Usage:
    source .venv/bin/activate
    uvicorn api:app --reload
    curl -X POST localhost:8000/disputes -H 'content-type: application/json' \
        -d '{"case_type": "item_not_received", "dispute_text": "..."}'
"""

from __future__ import annotations

from dotenv import load_dotenv

# Load .env before importing anything from `agent` — Langfuse (imported by
# agent.runner) reads its credentials from the environment the first time
# its client is constructed.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agent.case_types import CASE_TYPES  # noqa: E402
from agent.runner import run_dispute  # noqa: E402
from agent.state import CaseType  # noqa: E402

app = FastAPI(title="Dispute Adjudication Agent")


class DisputeRequest(BaseModel):
    case_type: CaseType
    dispute_text: str


class DisputeResponse(BaseModel):
    verdict: str | None
    verdict_confidence: float | None
    verdict_probabilities: dict[str, float] | None
    severity_score: float | None
    severity_confidence: float | None
    status: str | None
    notes: str | None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/case-types")
def case_types() -> dict:
    return {key: info["label"] for key, info in CASE_TYPES.items()}


@app.post("/disputes", response_model=DisputeResponse)
def adjudicate(request: DisputeRequest) -> DisputeResponse:
    result = run_dispute(request.dispute_text, request.case_type, channel="api")
    return DisputeResponse(**result)
