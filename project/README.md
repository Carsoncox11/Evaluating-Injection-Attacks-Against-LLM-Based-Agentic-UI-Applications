# Evaluating Injection Attacks Against LLM-Based Agentic UI Applications

A lightweight agent-powered UI that serves as a testbed to evaluate
agentic AI systems against three vectors of prompt injection: direct
injection, indirect injection, and UI Context Spoofing. Built for the
CIS 6614 group project (see the Overleaf proposal for the full writeup).

## Status (project milestone)

Working so far: the agent loop, both tools (`webpage_reader`,
`document_reader`), and a harness that runs an 8-payload **direct
injection** suite against the agent and reports Attack Success Rate
(ASR). This is the "minimum to stand on for the milestone" from
Carson's message in the group chat.

Not built yet: indirect injection and UI Context Spoofing harnesses,
Task Success / response-correctness scoring, the cross-model comparison,
and Floriano's full 104-scenario payload set (the 8 payloads here are a
starter set with the same shape his can drop into).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your own ANTHROPIC_API_KEY
```

Without an API key, everything still runs against `MockLLMClient`, an
offline stand-in used only to exercise the code paths. Its output is
**not** real model behavior and must not be used in the report or
milestone writeup, it's there so the harness can be developed and
tested before anyone wires up a real key.

## Running it

Chat with the agent directly:

```bash
python -m agentic_ui.cli
```

Run the direct injection suite and get an ASR report:

```bash
python -m attacks.run_direct_injection
```

This writes `results/direct_injection_summary.md` (the ASR table) and
one full transcript per payload to `results/transcripts/*.json` (not
committed, see `.gitignore`).

Run the tests:

```bash
python -m pytest tests/
```

## Layout

```
agentic_ui/
  agent.py        # the tool-use loop (system prompt + user turn -> model -> tools -> model)
  llm_client.py    # AnthropicLLMClient (real) and MockLLMClient (offline dev only)
  tools.py         # webpage_reader, document_reader
  cli.py           # minimal REPL chat interface
attacks/
  direct_injection_payloads.py   # the 8 payloads + their success-detection logic
  run_direct_injection.py        # harness: runs payloads, computes ASR, writes results/
sample_documents/   # local files document_reader is allowed to read
results/            # ASR summary + per-payload transcripts (transcripts gitignored)
tests/               # tool unit tests, no LLM required
```

## Notes for the group

- **Carson**: `tools.py` has a first working pass at both tools. The
  `TOOLS` schema list and `DISPATCH` dict are the two things to keep in
  sync if you extend or replace them.
- **Floriano**: payloads just need `{id, name, user_message, detect}`
  (see `direct_injection_payloads.py`). `detect` takes the agent's
  `RunResult` and returns a bool. Happy to write an adapter if your
  104-scenario set is in a different shape.
- **Jaeseok**: `AnthropicLLMClient` reads the model name from
  `AGENT_MODEL` in `.env`, so the cross-model comparison from the
  proposal is a config change away, assuming the other models are also
  served through the Anthropic API. A genuinely different provider
  (OpenAI, etc.) would need its own client class matching the
  `create_message(system, messages, tools) -> AgentResponse` interface
  in `llm_client.py`.
- Indirect injection and UI Context Spoofing harnesses can follow the
  same pattern as `run_direct_injection.py`, the main difference is
  where the injected text lives (inside tool-fetched content vs. the
  user's direct message).
