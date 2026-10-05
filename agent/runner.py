"""Shared entry point for running the dispute agent with Langfuse tracing.

Both the FastAPI service (api.py), the Streamlit UI (streamlit_app.py), and
the CLI demo (main.py) call `run_dispute()` instead of building/invoking the
graph themselves, so tracing, masking, and graph construction stay in one
place and every entry point is traced the same way.

Requires `load_dotenv()` to have already run in the caller *before* this
module is imported — Langfuse reads its credentials from the environment
the first time the client is constructed.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any

import certifi
from langfuse import Langfuse, get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from agent.graph import build_graph
from agent.state import CaseType, DisputeState

# Best-effort redaction for obvious PII/financial identifiers before any
# input/output/metadata leaves the process. This is a demo-grade regex mask,
# not a substitute for a real PII-detection pipeline in production.
_CARD_NUMBER_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        value = _CARD_NUMBER_RE.sub("[REDACTED_CARD_NUMBER]", value)
        value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
        return value
    if isinstance(value, dict):
        return {k: _redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_redact(v) for v in value)
    return value


def _mask(*, data: Any, **_kwargs: Any) -> Any:
    return _redact(data)


@lru_cache(maxsize=1)
def _configure_langfuse() -> None:
    # Langfuse's OTLP exporter falls back to a bare urllib3.PoolManager()
    # with no `ca_certs` when no custom requests.Session is supplied, so it
    # relies on OpenSSL's compiled-in default CA directory rather than
    # certifi — which is empty on python.org's macOS builds (the classic
    # "unable to get local issuer certificate" error) even though certifi
    # itself (used by httpx/requests elsewhere in this app) verifies fine.
    # Pointing the OTLP exporter at certifi's bundle explicitly fixes this
    # without needing a system-wide cert install.
    os.environ.setdefault("OTEL_EXPORTER_OTLP_CERTIFICATE", certifi.where())

    # Constructing the client explicitly (once) is what lets us attach a
    # mask function; a bare get_client() would build an unmasked default.
    Langfuse(mask=_mask)


@lru_cache(maxsize=1)
def _graph():
    return build_graph()


@lru_cache(maxsize=1)
def _callback_handler() -> CallbackHandler:
    return CallbackHandler()


def run_dispute(
    dispute_text: str, case_type: CaseType, *, channel: str = "cli"
) -> DisputeState:
    """Run one dispute through the LangGraph agent, traced in Langfuse.

    Args:
        dispute_text: the raw dispute narrative.
        case_type: one of the case types in agent/case_types.py.
        channel: which entry point this came through ("cli", "api",
            "streamlit") — recorded as a trace tag so traces can be filtered
            by surface in the Langfuse UI.

    Requires LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY (and optionally
    LANGFUSE_HOST) in the environment; if they're unset, the Langfuse
    client simply no-ops instead of raising.
    """
    _configure_langfuse()

    try:
        with propagate_attributes(
            trace_name="dispute-adjudication",
            tags=[f"channel:{channel}", f"case_type:{case_type}"],
        ):
            result = _graph().invoke(
                {"case_type": case_type, "dispute_text": dispute_text},
                config={
                    "callbacks": [_callback_handler()],
                    "run_name": "dispute-adjudication",
                },
            )
    finally:
        # Make sure traces are sent before a short-lived process (API
        # request handler, Streamlit script run, CLI run) exits.
        get_client().flush()

    return result
