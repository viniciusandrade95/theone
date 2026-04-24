# epic_04_rescheduling Test Report

## Test Strategy

Tests exercise the new internal assistant workflow endpoints through FastAPI TestClient and verify real CRM appointment state changes.

## Unit Tests Added

No pure unit tests were added in TheOne. The change is endpoint/repository integration behavior.

## Integration Tests Added

Added `tests/api/test_assistant_workflows_reschedule.py` covering:

- reschedule request updates an existing appointment
- reschedule can resolve exactly one upcoming appointment without explicit reference
- conflicting new slot returns `appointment_overlap`
- ambiguous target returns `appointment_ambiguous`

## Manual Test Scenarios

1. Create one future appointment for a tenant.
2. Ask chatbot1 through TheOne: `quero remarcar meu corte para amanhã às 16h17`.
3. Confirm with `sim, pode confirmar`.
4. Verify `/crm/appointments` shows the same appointment id with updated `starts_at` / `ends_at`.
5. Repeat with an occupied target slot and verify conflict text instead of success.

## Results

Command:

```bash
cd workspace/theone
venv/bin/python -m pytest tests/api/test_assistant_workflows_reschedule.py -q
```

Result:

```text
4 passed in 4.30s
```

System Python note:

```bash
cd workspace/theone
pytest tests/api/test_assistant_workflows_reschedule.py -q
```

Result:

```text
blocked: system Python lacks httpx, which FastAPI TestClient requires.
```

## Regressions Checked

- Tenant mismatch is still rejected.
- Assistant token auth is reused.
- Appointment overlap policy remains enforced by `AppointmentsRepo`.
- Existing public CRM appointment update route was not changed.

## Remaining Gaps

- Live deployed callback was not executed in this turn.
- No endpoint returns a list of ambiguous candidate appointments yet.
- Short display references are not mapped to CRM ids.
