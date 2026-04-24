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

Follow-up hardening added:
- retry handling for transient theone-wrapped chatbot 502 responses
- per-step retry attempt recording
- configurable `--step-delay` and `--scenario-delay`
- failure categories for upstream runtime, product assertion, and CRM verification failures
- stricter CRM verification matching to avoid stale appointment false positives
- summary sections that separate infrastructure instability from product logic failures
- `start_new` support for first-turn scenario execution so eval scenarios do not inherit stale dashboard/chatbot session state
- semantic reply substring alternatives through `expected_reply_contains_any`, used where several valid confirmation-summary phrasings are acceptable
- explicit `allow_rag_detour` support so an FAQ interruption can route through RAG without being counted as abandoned workflow when later steps prove booking state was preserved
- explicit forbidden workflow checks through `expected_workflow_not`, used to keep scenarios strict on no unexpected `handoff_to_human`
- rolling CRM appointment windows such as `relative:tomorrow_start_utc`, plus `match.start_time`, so scenarios using `amanhã` verify the correct time and a recent record instead of stale hard-coded dates

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
- A theone `VALIDATION_ERROR` with `details.message="Chatbot service request failed"` and `details.status=502` is treated as transient infrastructure and retried.
- CRM appointment verification now requires date/time, service evidence, and a recent-created window. Weak verification is marked `PARTIAL` instead of being treated as product proof.
- Scenarios with only upstream runtime failures or CRM verification uncertainty are classified as `PARTIAL`; deterministic assertion failures remain `FAIL`.
- Hybrid eval sends `start_new=true` on the first step of every scenario. The theone proxy resets the scoped dashboard conversation before forwarding that turn upstream, while later turns keep reusing `conversation_id` and `session_id`.
- Scenario expectations stay strict on route, workflow, slot preservation, missing-data guardrails, and no RAG/handoff fallback, but avoid brittle checks for one exact confirmation word when the assistant clearly returns a confirmation summary.
- Empty-slot `collecting` is allowed only when a scenario explicitly expects collection, so vague first turns such as `Quero marcar` are not misclassified as resets.
- `booking_missing_phone` now reflects the intended missing-data order: collect customer name first when no customer identity exists, then collect phone before any prebook execution.
- `booking_happy_path_full` accepts confirmation-summary wording instead of requiring the exact word `confirmar`, and verifies CRM side effects by recent creation, service UUID, and start time.
- `booking_missing_name` now accepts the real name-first flow: after the name is supplied, the assistant may summarize again before asking for phone on the next confirmation.
- `booking_with_fragmented_inputs` treats progressive service/date/time collection as valid, accepts confirmation-summary wording that may use `confirmação`, `tudo certo`, `posso encaminhar`, or `pré-agendamento`, and includes the final confirmation/execution step.
- `booking_interrupted_then_resume` allows a temporary RAG/FAQ detour only when the following step resumes `book_appointment` with preserved slots.

## Behavior Before
Validation depended on one-off curl commands and manual interpretation. Conversation IDs, session IDs, trace IDs, CRM verification, and transcripts were not captured in a durable repeatable format.

## Behavior After
An engineer can run deterministic-only or judge-enhanced evaluation against any deployed theone base URL and get structured artifacts:
- `summary.json`
- `summary.md`
- `raw_runs.json`
- `scenario_results/<scenario>.json`
- `scenario_results/<scenario>.md`

The runner also records retry attempts inside each step's `http.attempts` block and groups summary failures under:
- upstream/runtime
- product logic
- CRM verification

Each scenario starts from a fresh chatbot session even when the same deployed user/tenant/surface has previous dashboard conversation history.

## Risks / Follow-ups
- Scenario expectations may need tuning as assistant wording evolves.
- CRM verification currently supports appointment listing checks; additional CRM side-effect types can be added later.
- Judge mode depends on the sibling `chatbot1` repo or `CHATBOT1_REPO`.
- Live scenarios can create real appointments if pointed at production data, so use a known audit tenant.
- Render instability can still produce repeated upstream failures after retries; those are now visible as runtime failures instead of being mixed into product logic failures.
