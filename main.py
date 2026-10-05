"""Demo entry point for the dispute adjudication agent.

Runs one synthetic sample dispute for each of the four case types this
first version supports (see agent/case_types.py).

Usage:
    cp .env.example .env   # fill in TYPESAFE_API_KEY (and optionally
                           # LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY)
    source .venv/bin/activate
    python main.py
"""

from __future__ import annotations

from dotenv import load_dotenv

# Load .env before importing anything from `agent` — Langfuse (imported by
# agent.runner) reads its credentials from the environment the first time
# its client is constructed.
load_dotenv()

from agent.case_types import CASE_TYPES  # noqa: E402
from agent.runner import run_dispute  # noqa: E402


def main() -> None:
    for case_type, info in CASE_TYPES.items():
        print(f"=== {info['label']} ({case_type}) ===")
        result = run_dispute(info["sample_dispute"], case_type, channel="cli")

        print("Verdict:      ", result["verdict"])
        print("Confidence:   ", f"{result['verdict_confidence']:.2f}")
        print("Probabilities:", result["verdict_probabilities"])
        print("Severity:     ", f"{result['severity_score']:.2f}")
        print("Status:       ", result["status"])
        print("Notes:        ", result["notes"])
        print()


if __name__ == "__main__":
    main()
