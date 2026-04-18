# Epic Hybrid Eval Execution Log

## Goal
Build a production-oriented hybrid evaluation harness for the dashboard/WhatsApp chatbot path through theone.

## Problem Statement
The live assistant flow can regress in two different ways:
- deterministic operational regressions, such as lost session IDs, missing slots, stub execution, failed CRM callbacks, or absent CRM side effects
- conversational regressions, such as robotic wording, incoherent recovery, poor next questions, or confusing handling of interruptions

These concerns need separate evaluation. Backend correctness must not depend on an LLM judge.

## Root Cause
Manual curl-based validation proved useful but was not reproducible enough. The system needed a repeatable runner that saves the full request/response evidence and can optionally add soft quality scoring.

## Scope
Implemented a reusable Python runner that:
- loads reproducible JSON scenarios
- executes real multi-turn conversations through `POST /api/chatbot/message`
- reuses `conversation_id` and `session_id`
- stores raw requests, raw responses, parsed summaries, deterministic assertions, CRM verification, and optional judge output
- writes all run artifacts under `docs/test_runs/`
- supports no-judge, judge, fail-fast, and loop modes

## Files Changed
- `scripts/__init__.py`
- `scripts/chatbot_hybrid_eval.py`
- `docs/test_runs/scenarios/core_booking_scenarios.json`
- `docs/test_runs/judge_prompt.md`
- `tests/unit/test_chatbot_hybrid_eval.py`
- `docs/execution/epic_hybrid_eval_execution_log.md`
- `docs/execution/epic_hybrid_eval_test_report.md`
- `docs/execution/epic_hybrid_eval_examples.md`

## Design Decisions
- Deterministic checks are the source of truth for correctness.
- LLM-as-judge is disabled by default and only evaluates conversational quality.
- The runner reuses `chatbot1`'s existing `app.config.LLMClient` when judge mode is enabled.
- The runner uses standard-library HTTP so it can run without adding dependencies.
- Scenario outputs are written per scenario to make failures easy to inspect later.
- CRM verification is optional per scenario because not every scenario should create a record.
- Malformed API responses, HTTP errors, CRM errors, and malformed judge output are saved instead of crashing the full run.

## Behavior Before
Validation depended on one-off curl commands and manual interpretation. Conversation IDs, session IDs, trace IDs, CRM verification, and transcripts were not captured in a durable repeatable format.

## Behavior After
An engineer can run deterministic-only or judge-enhanced evaluation against any deployed theone base URL and get structured artifacts:
- `summary.json`
- `summary.md`
- `raw_runs.json`
- `scenario_results/<scenario>.json`
- `scenario_results/<scenario>.md`

## Risks / Follow-ups
- Scenario expectations may need tuning as assistant wording evolves.
- CRM verification currently supports appointment listing checks; additional CRM side-effect types can be added later.
- Judge mode depends on the sibling `chatbot1` repo or `CHATBOT1_REPO`.
- Live scenarios can create real appointments if pointed at production data, so use a known audit tenant.
