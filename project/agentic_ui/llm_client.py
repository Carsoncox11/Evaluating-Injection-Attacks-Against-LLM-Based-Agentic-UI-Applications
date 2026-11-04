"""LLM backend for the agent.

Two clients, same interface (`.create_message(system, messages, tools) ->
AgentResponse`):

- AnthropicLLMClient: the real thing. Needs ANTHROPIC_API_KEY (see
  .env.example). Swapping AGENT_MODEL in .env is all that's needed for
  the cross-model comparison described in the proposal, as long as the
  other model is also available through the Anthropic API; a genuinely
  different provider (e.g. OpenAI) would need its own client class
  implementing the same interface, which is the intended extension
  point for Jaeseok's analysis pass.

- MockLLMClient: NOT a real model. It exists only so the rest of the
  testbed (tools, agent loop, attack harness) can be exercised and
  demoed with no API key and no network calls. Its "decisions" are
  simple keyword rules, not an LLM's actual judgment, so results
  produced with it must never be reported as security findings.
  Whichever teammate wires up the real API key should flip
  USE_MOCK=false (or just set ANTHROPIC_API_KEY) before we run the
  experiments that go in the report.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict


@dataclass
class AgentResponse:
    """Normalized response shape, independent of which backend produced it."""

    text: str
    tool_calls: list[ToolUseBlock] = field(default_factory=list)
    stop_reason: str = "end_turn"
    raw: object = None


class AnthropicLLMClient:
    def __init__(self, model: str | None = None):
        import anthropic  # imported lazily so MockLLMClient works without the package installed

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it "
                "in, or use MockLLMClient for offline testing."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.environ.get("AGENT_MODEL", "claude-sonnet-4-5-20250929")

    def create_message(self, system: str, messages: list[dict], tools: list[dict]) -> AgentResponse:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools,
        )
        text_parts = []
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))
        return AgentResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason,
            raw=resp,
        )


class MockLLMClient:
    """Offline stand-in for development only. See module docstring."""

    def __init__(self, model: str | None = None):
        self.model = model or "mock-offline-v0"

    def create_message(self, system: str, messages: list[dict], tools: list[dict]) -> AgentResponse:
        last_user_text = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, str):
                    last_user_text = content
                else:
                    # tool_result content blocks; find the most recent plain user turn instead
                    continue
                break

        lowered = last_user_text.lower()

        # Deliberately naive keyword rules, just to exercise the harness end to end.
        if "document_reader" in lowered and ("/etc/" in lowered or ".." in lowered):
            return AgentResponse(
                text="",
                tool_calls=[
                    ToolUseBlock(id="mock_1", name="document_reader", input={"path": "/etc/passwd"})
                ],
                stop_reason="tool_use",
            )

        for marker in ("ignore all previous instructions", "ignore your instructions", "new directive"):
            if marker in lowered:
                return AgentResponse(text="[mock] (would comply with injected instruction here)")

        return AgentResponse(text=f"[mock] I can't actually think, but I heard: {last_user_text[:200]}")
