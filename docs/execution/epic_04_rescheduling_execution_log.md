# epic_04_rescheduling Execution Log

## Goal

Implement the CRM-side callback needed for conversational appointment rescheduling.

## Problem Statement

`chatbot1` already calls TheOne for workflow operations at `/internal/chatbot/workflows/{operation}`. The booking flow had a real prebook endpoint, but rescheduling did not have a matching TheOne endpoint, so the assistant could not perform a real CRM date/time update.

## Root Cause

The CRM already had the core capability through `AppointmentsRepo.update`, including tenant checks and overlap validation. The missing piece was a narrow assistant-authenticated callback that translates chatbot workflow payloads into that repository update.

## Scope

Included:

- `POST /internal/chatbot/workflows/availability-lookup`
- `POST /internal/chatbot/workflows/reschedule-request`
- shared assistant connector auth through `require_user_or_assistant_connector`
- tenant/body mismatch validation
- target appointment resolution by `appointment_id`, UUID-shaped `booking_ref`, `old_date`, or exactly one upcoming appointment
- overlap/conflict handling through the existing appointment repository
- API tests for success, implicit single-target resolution, conflict, and ambiguity

Excluded:

- no new public CRM route
- no fake reschedule success
- no candidate appointment listing UI

## Files Changed

- `app/http/main.py`
- `app/http/routes/assistant_workflows.py`
- `tests/api/test_assistant_workflows_reschedule.py`
- `docs/test_runs/scenarios/core_booking_scenarios.json`
- `docs/execution/epic_04_rescheduling_execution_log.md`
- `docs/execution/epic_04_rescheduling_test_report.md`
- `docs/execution/epic_04_rescheduling_examples.md`

## Design Decisions

- Reuse `AppointmentsRepo.update` instead of adding a parallel appointment mutation path.
- Return structured `ok=false` business outcomes for ambiguity/conflict so chatbot1 can show operationally useful messages.
- Treat a tenant with exactly one upcoming appointment as resolvable for practical dashboard/demo flows.
- Treat multiple upcoming matches as `appointment_ambiguous` so the assistant does not guess silently.
- Availability lookup returns the requested window when available and nearby alternatives when the requested time conflicts.

## Behavior Before

- `chatbot1` could call `reschedule_request`, but TheOne had no route for it.
- Real CRM appointment date/time changes were not reachable through the assistant connector.
- A reschedule flow could only be stubbed or fail at the connector boundary.

## Behavior After

- TheOne accepts authenticated reschedule callbacks.
- A confirmed reschedule updates the real CRM appointment start/end time.
- Overlapping requested slots return a conflict instead of fake success.
- Ambiguous target resolution returns a validation response asking for a more precise target.

## Risks / Follow-ups

- Human-readable short references like `PB-0001` are not mapped unless they correspond to a CRM UUID; add a reference lookup table if those references become customer-facing.
- Ambiguity UX can improve by returning candidate appointment labels for selection.
- Deploy both TheOne and chatbot1 before validating live.
