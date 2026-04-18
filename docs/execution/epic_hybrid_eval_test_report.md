# Epic Hybrid Eval Test Report

## Test Strategy
The tests validate the harness itself without calling live theone, chatbot1, CRM, or LLM services. HTTP and judge paths are mocked where needed.

## Harness Tests Added
- scenario loading from `docs/test_runs/scenarios/core_booking_scenarios.json`
- nested chatbot response parsing
- deterministic assertion failures for stub execution and missing slots
- transcript construction from multi-turn step records
- malformed judge output handling
- judge mode with mocked structured JSON
- summary generation with failure patterns and judge issues
- no-judge scenario execution with conversation/session reuse
- run summary output generation

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
- required slots
- action result fields
- unexpected RAG reset
- `prebooking_stub` leakage in real-tenant scenarios
- optional CRM appointment side effects

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

## Remaining Gaps
- Live API execution is not covered by unit tests.
- CRM verification currently focuses on `/crm/appointments`.
- The LLM judge prompt is covered structurally, not by a real model call in CI.
