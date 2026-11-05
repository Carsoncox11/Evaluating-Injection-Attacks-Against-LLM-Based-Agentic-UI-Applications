# Evaluating Injection Attacks Against LLM-Based Agentic UI Applications

A lightweight agent-powered UI that serves as a testbed to evaluate agentic AI systems against three main vectors of prompt injection: direct injection, indirect injection, and UI Context Spoofing. Built for the CIS 6614 (Advanced Software Systems Security) group project at the University of Central Florida, Fall 2026.

## Team

- Emanuel Botros (Team Lead)
- Jaeseok Choi (Evaluation and Analysis)
- Floriano Costa Neto (Injection Designer)
- Carson Cox (Tool Developer)

## Repository layout

- [`project/`](project/) — the agentic UI testbed, tools, direct injection harness, tests, and milestone results. Start here to run the code; see `project/README.md` for setup and usage.
- [`test_suite/`](test_suite/) — the proposed 122-scenario test suite (spreadsheet + guide) covering all three injection vectors across both evaluation rounds.

## Status

Working so far: the agent loop, both tools (`webpage_reader`, `document_reader`), and a harness that runs an 8-payload direct injection suite against the agent and reports Attack Success Rate (ASR). The milestone report's initial result (12.5% ASR, 1/8) is reproduced in `project/results/direct_injection_summary.md`.

Not yet built: indirect injection and UI Context Spoofing harnesses, Task Success / response-correctness scoring, the spreadsheet runner for the full 122-scenario suite, and the cross-model comparison across the models proposed in `test_suite/README.md`.

See the full milestone writeup (Overleaf) for the complete problem statement, techniques, expected outcomes, and discussion.
