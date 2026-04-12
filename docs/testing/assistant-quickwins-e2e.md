# Assistant quick wins — E2E tests

This repo ships API-driven end-to-end tests that validate **real backend side effects** for the assistant quick wins increment:

1) slot suggestions (availability)
2) handoff-to-human (durable record + CRM interaction)

## How to run

```bash
venv/bin/pytest -q tests/api/test_assistant_quickwins_e2e.py
```

These tests run with `ENV=test` + `DATABASE_URL=dev` (in-memory SQLite) and seed deterministic tenants/services/locations/booking settings via API calls.

## What is validated

### Flow 1: user asked for a time slot

- First turn missing required info triggers a deterministic follow-up question.
- Second turn returns **3–5 real slots** sourced from the existing public booking availability engine.
- Session continuity is persisted in `chatbot_conversation_sessions.state_payload/context_payload`.
- Turn history is persisted in `chatbot_conversation_messages`.

### Flow 2: user asked to talk to an attendant

- A handoff request results in a durable row in `assistant_handoffs`.
- A CRM interaction is created (`interactions.type = "assistant_handoff"`) when customer context is available.
- The user-facing response confirms the handoff.
- Internal visibility works via `GET /crm/assistant/handoffs`.
- Repeated handoff intent in the same conversation does not create uncontrolled duplicates.

## Known limitations

- Upstream chatbot intent/slot extraction is mocked in tests (the assistant logic in `theone` remains deterministic and shallow by design).
- Slot suggestions are limited to a single day (the `public_booking` source-of-truth behavior).
- Handoff lifecycle beyond `open` visibility (claim/close) is intentionally deferred.

