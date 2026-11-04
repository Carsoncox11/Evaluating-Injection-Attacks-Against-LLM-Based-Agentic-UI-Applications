"""Run the direct injection payload suite against the agent and report
Attack Success Rate (ASR), per the metrics defined in the proposal.

    python -m attacks.run_direct_injection

Writes one JSON transcript per payload to results/transcripts/ and a
summary table to results/direct_injection_summary.md.

This only measures ASR for now (per the milestone scope: "get enough
working to do at minimum some basic example direct injection attacks").
Task Success (TS) and response-correctness scoring for the other two
vectors (indirect injection, UI context spoofing) are the natural next
step once Carson's tools and Floriano's full payload set are in.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_ui.agent import Agent  # noqa: E402
from agentic_ui.llm_client import AnthropicLLMClient, MockLLMClient  # noqa: E402
from attacks.direct_injection_payloads import PAYLOADS  # noqa: E402

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
TRANSCRIPTS_DIR = os.path.join(RESULTS_DIR, "transcripts")


def build_agent() -> tuple[Agent, bool]:
    load_dotenv()
    using_mock = not bool(os.environ.get("ANTHROPIC_API_KEY"))
    client = MockLLMClient() if using_mock else AnthropicLLMClient()
    return Agent(client), using_mock


def main() -> None:
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    agent, using_mock = build_agent()

    if using_mock:
        print(
            "!! No ANTHROPIC_API_KEY set — running against MockLLMClient. !!\n"
            "!! These results are NOT real and must not go in the report. !!\n"
            "!! Set ANTHROPIC_API_KEY in .env and re-run for real data.   !!\n"
        )

    rows = []
    for payload in PAYLOADS:
        result = agent.run_turn(payload.user_message)
        succeeded = payload.detect(result)
        rows.append((payload, succeeded))

        transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{payload.id}.json")
        with open(transcript_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "payload_id": payload.id,
                    "payload_name": payload.name,
                    "user_message": payload.user_message,
                    "model": agent.llm_client.model,
                    "using_mock": using_mock,
                    "attack_succeeded": succeeded,
                    "final_text": result.final_text,
                    "tool_calls_made": result.tool_calls_made,
                    "transcript": [
                        {"role": t.role, "content": t.content, "tool_name": t.tool_name, "tool_input": t.tool_input}
                        for t in result.transcript
                    ],
                },
                fh,
                indent=2,
            )

        status = "SUCCEEDED (vulnerable)" if succeeded else "blocked"
        print(f"[{payload.id}] {payload.name}: {status}")

    asr = sum(1 for _, succeeded in rows if succeeded) / len(rows)

    summary_path = os.path.join(RESULTS_DIR, "direct_injection_summary.md")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("# Direct Injection Results\n\n")
        fh.write(f"Run at: {datetime.now(timezone.utc).isoformat()}Z\n\n")
        fh.write(f"Model: `{agent.llm_client.model}`" + (" (MOCK — not real data)\n\n" if using_mock else "\n\n"))
        fh.write(f"**Attack Success Rate (ASR): {asr:.0%}** ({sum(1 for _, s in rows if s)}/{len(rows)})\n\n")
        fh.write("| Payload ID | Name | Result |\n|---|---|---|\n")
        for payload, succeeded in rows:
            mark = "Succeeded" if succeeded else "Blocked"
            fh.write(f"| {payload.id} | {payload.name} | {mark} |\n")
        fh.write("\nFull transcripts: `results/transcripts/<payload_id>.json`\n")

    print(f"\nASR: {asr:.0%} ({sum(1 for _, s in rows if s)}/{len(rows)})")
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
