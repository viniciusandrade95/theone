# Autonomous Chatbot Test Runs

This directory is written by `scripts/chatbot_autonomous_tester.py`.

Run one deterministic smoke pass:

```bash
python3 scripts/chatbot_autonomous_tester.py \
  --base-url "$THEONE_BASE" \
  --tenant-id "$TENANT_ID" \
  --token "$THEONE_TOKEN" \
  --mode deterministic \
  --max-iterations 1
```

Run one hybrid pass with generated scenarios:

```bash
CHATBOT1_REPO=/home/vinicius/system-audit/workspace/chatbot1 \
python3 scripts/chatbot_autonomous_tester.py \
  --base-url "$THEONE_BASE" \
  --tenant-id "$TENANT_ID" \
  --token "$THEONE_TOKEN" \
  --mode hybrid \
  --max-iterations 1 \
  --generated-count 5
```

Run continuously:

```bash
CHATBOT1_REPO=/home/vinicius/system-audit/workspace/chatbot1 \
python3 scripts/chatbot_autonomous_tester.py \
  --base-url "$THEONE_BASE" \
  --tenant-id "$TENANT_ID" \
  --token "$THEONE_TOKEN" \
  --mode hybrid \
  --generated-count 5 \
  --step-delay 0.5 \
  --scenario-delay 2 \
  --loop-delay 30
```

Required runtime values:

- `THEONE_BASE`: deployed theone API/web base URL.
- `TENANT_ID`: tenant under test.
- `THEONE_TOKEN`: short-lived user bearer token for that tenant.
- `CHATBOT1_REPO`: optional path to the local chatbot1 repo when LLM generation or judge mode is used.

Expected structure:

```text
docs/test_runs/autonomous/
  rolling_summary.json
  top_failures.md
  iterations/
    0001-<timestamp-run-id>/
      generated_scenarios.json
      summary.json
      summary.md
      deterministic/
        scenario_results/
      generated/
        scenario_results/
```

The runner executes deterministic regression scenarios and generated noisy user conversations against the live API. It stores raw responses, parsed summaries, transcripts, deterministic assertion results, heuristic findings, optional judge output, and rolling failure statistics.

Do not commit secrets or bearer tokens into this directory.
