# Epic Autonomous Eval Test Report

## Test Strategy

The tests validate the autonomous harness without calling live theone, chatbot1, CRM, or LLM services. The live runner is built by composing the existing hybrid eval harness, so tests focus on the new behavior: generation fallback, scenario normalization, heuristic findings, rolling summaries, and iteration output.

## Unit Tests Added

- `test_generate_scenarios_falls_back_to_seed_when_llm_unavailable`
- `test_normalized_generated_booking_steps_get_operational_expectations`
- `test_heuristics_detect_slot_loss_and_premature_summary`
- `test_heuristics_allow_explicit_rag_detour`
- `test_rolling_summary_tracks_top_failures`
- `test_run_iteration_writes_generated_outputs`

## Integration Tests Added

No live-network integration test was added. The script is intended to run live from the command line with an explicit bearer token and audit tenant.

## Manual Test Scenarios

Recommended manual smoke run:

```bash
python3 scripts/chatbot_autonomous_tester.py \
  --base-url "$THEONE_BASE" \
  --tenant-id "$TENANT_ID" \
  --token "$THEONE_TOKEN" \
  --mode hybrid \
  --max-iterations 1 \
  --generated-count 2 \
  --output-dir docs/test_runs/autonomous_smoke
```

Expected:

- deterministic scenarios run first
- generated scenarios are saved
- live scenario results are saved
- `rolling_summary.json` and `top_failures.md` are created

## Results

Commands run:

```bash
pytest -q tests/unit/test_chatbot_autonomous_tester.py
pytest -q tests/unit/test_chatbot_hybrid_eval.py
python3 -m py_compile scripts/chatbot_autonomous_tester.py
python3 scripts/chatbot_autonomous_tester.py --help
```

Results:

```text
6 passed in 0.05s
18 passed in 0.08s
py_compile passed
CLI help passed
```

## Regressions Checked

- Existing hybrid eval unit tests still pass.
- Seed fallback works when the LLM is unavailable.
- Generated booking scenarios receive operational expectations.
- Explicit FAQ/RAG detours are not false failures.
- Slot loss and premature summary are flagged.
- Rolling summaries aggregate top failure patterns and bug types.
- Iteration output is written without live API access when scenario execution is mocked.

## Remaining Gaps

- CI/unit tests do not prove live API health.
- LLM scenario quality must be reviewed from generated output during initial runs.
- The heuristic layer is intentionally conservative and may flag product questions as leads requiring human triage.
