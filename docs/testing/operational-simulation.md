# Operational simulation and regression workflow

This project now treats operational simulation and bug reproduction as a repeatable QA discipline.

## Goals

- Simulate realistic salon operations: bookings, reschedules, cancellations, no-shows, and completed visits.
- Record every movement so a run can be replayed and audited later.
- Catalog every production bug or regression with a stable identifier.
- Add an automated regression test every time a new fix is merged.

## Required workflow for every newly discovered bug

1. Create or update an entry in `qa/error_catalog.json`.
2. Document:
   - bug id
   - date discovered
   - symptom
   - root cause
   - fix summary
   - automated regression test id(s)
3. Add or update at least one automated test under `tests/`.
4. Ensure the new test is part of the default pytest suite.
5. If the bug is operational, add a reproduction recipe or simulation step to this document or to the simulator manifest.

A bug fix is not complete until the catalog entry and regression test both exist.

## Deterministic operational simulation

Use `tasks/simulate_appointment_operations.py` to generate a deterministic run against a staging or production-like environment.

### What the simulator does

- authenticates through the public auth flow
- creates customers and services when requested
- creates appointments
- mutates appointments through lifecycle events
- records every successful and failed action to disk
- writes summary artifacts that can be replayed or diffed later

### Generated artifacts

Each run writes a timestamped directory under `artifacts/operational-simulations/<run_id>/` containing:

- `manifest.json`: run configuration and seed
- `actions.jsonl`: ordered action log
- `errors.jsonl`: ordered error log
- `summary.json`: totals, status distribution, and error counts

These artifacts are the reproducible trail for every run.

## Example command

```bash
python tasks/simulate_appointment_operations.py \
  --base-url https://your-frontend.onrender.com \
  --email qa-bot@example.com \
  --password secret123 \
  --tenant-name "QA Salon" \
  --seed 42 \
  --customers 25 \
  --services 6 \
  --appointments 150
```

The command above uses signup when the account does not exist yet, then simulates a run with a deterministic seed.

## Suggested lifecycle profile

A realistic first pass is:

- 60% completed
- 15% cancelled
- 10% no_show
- 10% rescheduled
- 5% left booked

This is only a starting point. Tune it as real usage data becomes available.

## Regression policy

At least one regression test should exist for:

- authentication and tenant bootstrapping
- default location creation
- appointment lifecycle transitions
- overlap validation
- analytics consistency after lifecycle mutations
- every production incident recorded in `qa/error_catalog.json`

## Current baseline regressions

- `tests/api/test_audit_soft_delete_api.py::test_soft_delete_restore_and_audit_log`
- `tests/api/test_appointment_operational_regressions.py::test_appointment_lifecycle_operational_flow`
- `tests/api/test_error_catalog.py::test_error_catalog_entries_reference_existing_tests`

## Notes

- Run simulations against staging by default.
- Use dedicated QA accounts and tenants.
- Do not point load-style runs at production without rate limits and monitoring.
- Keep simulation seeds when a run exposes a bug so the same sequence can be replayed.
