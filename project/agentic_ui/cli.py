"""Minimal chat REPL on top of Agent — the "UI" in agentic UI testbed.

    python -m agentic_ui.cli

Each line you type is one user turn (tool-use round trips happen
automatically and are shown inline). Type 'exit' or Ctrl-D to quit.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from .agent import Agent
from .llm_client import AnthropicLLMClient, MockLLMClient


def build_agent() -> Agent:
    load_dotenv()
    if os.environ.get("ANTHROPIC_API_KEY"):
        client = AnthropicLLMClient()
        print(f"[using Anthropic API, model={client.model}]")
    else:
        client = MockLLMClient()
        print("[no ANTHROPIC_API_KEY set — using MockLLMClient (offline demo mode, not a real model)]")
    return Agent(client)


def main() -> None:
    agent = build_agent()
    print("Agentic UI testbed. Type a message, or 'exit' to quit.\n")
    while True:
        try:
            user_message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit"}:
            break

        result = agent.run_turn(user_message)
        for turn in result.transcript:
            if turn.role == "tool_result":
                preview = turn.content[:200].replace("\n", " ")
                print(f"  [tool:{turn.tool_name}({turn.tool_input}) -> {preview}...]")
        print(f"agent> {result.final_text}\n")


if __name__ == "__main__":
    sys.exit(main())
