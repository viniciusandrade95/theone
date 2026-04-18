# Epic Hybrid Eval Test Report

## Test Strategy
The tests validate the harness itself without calling live theone, chatbot1, CRM, or LLM services. HTTP and judge paths are mocked where needed.

## Harness Tests Added
- scenario loading from `docs/test_runs/scenarios/core_booking_scenarios.json`
- nested chatbot response parsing
- deterministic assertion failures for stub execution and missing slots
- deterministic assertion support for semantic reply alternatives via `expected_reply_contains_any`
- transcript construction from multi-turn step records
- malformed judge output handling
- judge mode with mocked structured JSON
- summary generation with failure patterns and judge issues
- no-judge scenario execution with conversation/session reuse
- run summary output generation
- transient chatbot 502 retry behavior
- stale CRM appointment non-match behavior
- weak CRM matching classified as partial
- summary markdown separated by failure category
- theone proxy `start_new` behavior resets stale scoped session before the first eval turn

## Scenario Coverage
The seeded scenario file covers:
- happy-path booking
- missing customer name
- missing customer phone
- conflict or unavailable slot behavior
- interruption and resume
- user changes time mid-flow
- FAQ then booking
- short affirmations
- fragmented input
- colloquial PT-BR input

## Deterministic Coverage
The runner checks:
- HTTP success
- JSON parseability
- workflow route
- workflow name
- response/workflow status
- reply contains / not contains
- reply contains any acceptable phrase for semantic wording checks
- required slots
- action result fields
- unexpected RAG reset
- `prebooking_stub` leakage in real-tenant scenarios
- optional CRM appointment side effects
- retry attempts for theone-wrapped upstream 502 responses
- failure category classification

## Judge Coverage
Judge tests cover:
- malformed non-JSON output saved as failed evidence
- valid structured judge output accepted
- score and schema validation

## Results
Focused command:

```bash
pytest tests/unit/test_chatbot_hybrid_eval.py
```

Expected result: all harness tests pass.

## Regressions Checked
- no-judge mode works without importing `chatbot1`
- judge mode uses mocked existing LLM client shape
- conversation ID and session ID are reused on later turns
- summary files are generated
- one transient upstream 502 can recover on retry
- old appointments are not accepted as proof of a new scenario run
- infra/runtime, product assertion, and CRM verification failures are reported separately
- first-turn scenario requests can force a fresh chatbot session, preventing stale state from causing premature summaries
- `booking_with_fragmented_inputs` accepts valid progressive collection and confirmation-summary wording without requiring one exact word.
- `booking_missing_phone` follows the current product guardrail sequence: missing name first, then missing phone.
- Expected `collecting` steps with empty slots are not treated as resets; unexpected empty-slot collection is still flagged.

## Remaining Gaps
- Live API execution is not covered by unit tests.
- CRM verification currently focuses on `/crm/appointments`.
- The LLM judge prompt is covered structurally, not by a real model call in CI.
