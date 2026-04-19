# Epic Autonomous Eval Execution Log

## Goal

Build a continuous chatbot evaluation loop that repeatedly runs known regression scenarios, generates new noisy conversations, executes them against the live theone chatbot API, evaluates the responses, and stores failure evidence without manual intervention.

## Problem Statement

The existing hybrid eval harness can run deterministic scenarios, but it only tests scenarios humans already wrote. Conversational systems regress in edge cases that are hard to enumerate manually: fragmented inputs, typos, interruptions, ambiguous remarcação/cancellation phrasing, repeated corrections, and colloquial PT-BR. We need a loop that keeps probing those areas and aggregates failures.

## Root Cause

Manual and one-shot harness runs do not produce enough adversarial variation. They also require a human to decide what to try next. The system needed a generation layer, heuristic post-processing, and rolling summaries on top of the deterministic harness.

## Scope

Included:

- New `scripts/chatbot_autonomous_tester.py`.
- Deterministic/generative/hybrid run modes.
- LLM scenario generation through the existing chatbot LLM integration reused by the hybrid eval judge path.
- Seed fallback scenarios when LLM generation is unavailable.
- Live scenario execution by reusing `scripts/chatbot_hybrid_eval.py`.
- Heuristic failure checks for slot loss, unexpected RAG, unexpected handoff, premature summaries, repeated questions, fake success, dead ends, and final-status mismatch.
- Iteration output under `docs/test_runs/autonomous/iterations/`.
- Rolling summary files:
  - `docs/test_runs/autonomous/rolling_summary.json`
  - `docs/test_runs/autonomous/top_failures.md`
- Unit tests for generation fallback, normalization, heuristics, rolling summaries, and mocked iteration execution.

Excluded:

- No new live API credentials are stored.
- No new third-party dependencies.
- No replacement of deterministic checks with LLM judging.
- No direct CRM mutation beyond whatever the selected live scenarios already do through the existing API.

## Files Changed

- `scripts/chatbot_autonomous_tester.py`
- `tests/unit/test_chatbot_autonomous_tester.py`
- `docs/test_runs/autonomous/README.md`
- `docs/execution/epic_autonomous_eval_execution_log.md`
- `docs/execution/epic_autonomous_eval_test_report.md`
- `docs/execution/epic_autonomous_eval_examples.md`

## Design Decisions

- Reuse `chatbot_hybrid_eval.run_scenario` for live execution, transcript capture, deterministic assertions, CRM verification, and optional judge execution.
- Keep generation separate from execution. Generated scenarios are written to `generated_scenarios.json` before they are run.
- Use `mode=hybrid` by default so each iteration runs known regressions plus generated probes.
- Add default delays between steps, scenarios, and loop iterations to avoid hammering Render or the chatbot service.
- Use seed scenarios when the LLM is unavailable so the loop still exercises the live system.
- Apply heuristic checks after each scenario result and rewrite the scenario output with those findings included.
- Maintain rolling summaries across the latest 100 iterations to expose frequent failure classes and user-pattern failures.

## Behavior Before

- Engineers could run one deterministic scenario pack with optional judge scoring.
- New edge cases had to be manually written into the scenario file.
- Failure aggregation was per-run only.

## Behavior After

- Engineers can run an autonomous loop that alternates deterministic and generated scenarios.
- Every iteration stores generated inputs, transcripts, deterministic failures, heuristic failures, optional judge output, and a summary.
- Rolling summaries expose the top failure patterns and most frequent bug types over time.

## Risks / Follow-ups

- LLM-generated scenarios may be too strict or too loose; heuristic findings are intended as leads, not final product verdicts.
- Live generated scenarios can create CRM side effects. Run against the audit tenant only.
- The loop is intentionally conservative about pacing, but long runs still consume API/LLM capacity.
- Some generated remarcação/cancellation scenarios depend on live CRM fixture state and may be `PARTIAL` or `FAIL` until those flows are fully fixture-backed.
