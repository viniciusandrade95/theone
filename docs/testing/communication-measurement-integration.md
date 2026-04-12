# Communication + measurement sprint: integration validation

This doc describes how to validate (locally) that the sprint’s core outcomes work together:

- automatic confirmations (assistant prebook + handoff)
- outbound provider delivery lifecycle + callback safety
- assistant funnel analytics sufficient for ROI conversations

## Recommended test runs

Run the integrated flow tests:

```bash
venv/bin/pytest -q tests/api/test_comm_measurement_integration_api.py
```

Run the supporting suites:

```bash
venv/bin/pytest -q \
  tests/api/test_assistant_auto_confirmations_api.py \
  tests/api/test_assistant_analytics_api.py \
  tests/api/test_outbound_provider_lifecycle_api.py
```

## What the integration tests validate

### Prebook confirmation flow
- `POST /crm/assistant/prebook` creates a pending appointment
- automatic confirmation is triggered and creates an `outbound_messages` row (`trigger_type=assistant_prebook_created`)
- provider-backed WhatsApp send succeeds deterministically in test (mocked) and sets:
  - `status=sent`, `delivery_status=accepted`, `provider_message_id`
- provider callback via `POST /messaging/delivery` updates the message to `delivery_status=delivered` and sets `delivered_at`
- duplicate callback is deduped via `(tenant_id, provider, external_event_id)` and does not create extra rows
- assistant funnel events are emitted (`assistant_prebook_requested`, `assistant_prebook_created`)
- confirming the appointment (`PATCH /crm/appointments/{id}` to `status=booked`) emits `assistant_conversion_confirmed`
- `/analytics/assistant/overview` reflects expected counts and conversion rate
- callback routing is tenant-safe (wrong tenant’s `phone_number_id` cannot update another tenant’s outbound message)

### Handoff confirmation flow
- `POST /api/chatbot/message` produces a handoff request (mocked upstream)
- a durable handoff record is created (`assistant_handoffs`) and a CRM interaction is written (`assistant_handoff`)
- automatic confirmation attempts WhatsApp first, fails deterministically (no tenant WhatsApp account), and falls back to email
- repeated handoff intent in the same conversation does not create duplicates (handoff or confirmations)
- `/analytics/assistant/overview` reflects message + handoff counts

## Operational notes (rollout readiness)

Success indicators:
- outbound confirmations show `status=sent` and `delivery_status=accepted` (provider-backed) or `delivery_status=sent` (SMTP)
- callbacks move WhatsApp messages to `delivery_status=delivered/read`
- assistant analytics shows non-zero `prebook_created`, `handoff_created`, and `conversion_confirmed` where applicable

Failure indicators:
- missing templates: no confirmation rows created; logs emit `assistant_confirmation_failed`
- missing provider config: confirmation rows created as `failed` with `error_code=provider_not_configured`
- missing recipient: confirmation rows `failed` with `error_code=missing_recipient`

Known limitations (outside this sprint):
- quote/consult funnel events are defined but not emitted until durable quote/consult objects exist
- email delivery callbacks (delivered/opened/bounced) are not implemented; SMTP is “sent-only”

