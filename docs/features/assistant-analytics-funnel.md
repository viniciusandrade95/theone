# Assistant analytics & minimum funnel (v1)

## Why this exists
Assistant ROI cannot be measured reliably via generic booking analytics alone.

This feature adds a **business-level funnel event stream** for assistant outcomes (messages → handoff/prebook → conversion), plus assistant-focused analytics endpoints.

It is intentionally not an external BI stack.

## Funnel events vs technical telemetry

### Funnel events (business)
Stored in `assistant_funnel_events` and designed for ROI questions:
- how many conversations did the assistant handle?
- how many became handoff/prebook?
- how many prebooks were confirmed (conversion)?

Key rules:
- tenant-scoped on every write and query
- event taxonomy is explicit + finite (see below)
- prefer persisted artifacts (handoff/prebook/appointment updates) over “inferred text”

### Technical telemetry (ops)
Prometheus metrics and structured logs remain the place for operational reliability:
- outbound send success/failure by channel/provider (`outbound_send_total`)
- delivery callback outcomes (`outbound_delivery_events_total`)

## Event taxonomy (v1)

Implemented events (this PR):
- `assistant_message_received` (chat proxy)
- `assistant_message_replied` (chat proxy)
- `assistant_fallback` (when handoff is requested for a non-user-request reason)
- `assistant_handoff_requested` (deduped per `conversation_id + conversation_epoch`)
- `assistant_handoff_created` (deduped per `handoff_id`)
- `assistant_prebook_requested` (deduped per `idempotency_key` when provided)
- `assistant_prebook_created` (deduped per `appointment_id`)
- `assistant_conversion_confirmed` (deduped per `appointment_id`)

Defined but not yet emitted (awaiting durable domain objects):
- `assistant_quote_requested`, `assistant_quote_created`
- `assistant_consult_requested`, `assistant_consult_created`

## Attribution fields

`assistant_funnel_events` stores:
- `tenant_id`, `trace_id`
- `conversation_id`, `assistant_session_id`
- `customer_id`
- `event_name`, `event_source`, `channel`
- `related_entity_type`, `related_entity_id`
- `dedupe_key` (optional unique within tenant)
- `metadata` (small JSON payload)

## Analytics endpoints

All assistant analytics endpoints are tenant-scoped and require staff auth:

- `GET /analytics/assistant/overview?from=<dt>&to=<dt>`
- `GET /analytics/assistant/funnel?from=<dt>&to=<dt>`
- `GET /analytics/assistant/channels?from=<dt>&to=<dt>` (assistant-triggered outbound only)
- `GET /analytics/assistant/templates?from=<dt>&to=<dt>` (assistant-triggered outbound only)
- `GET /analytics/assistant/conversions?from=<dt>&to=<dt>`

Date range is interpreted as UTC for storage and filtering.

## Integration validation

See `docs/testing/communication-measurement-integration.md` for end-to-end integration coverage that validates:
- assistant events → confirmations → delivery callbacks
- funnel event emission + analytics correctness

## Interpreting “conversion”

For v1, conversion is defined as:

- an appointment created via `POST /crm/assistant/prebook` (tracked via `assistant_prebook_requests`)
- later updated from `status="pending"` → `status="booked"` by staff, and `needs_confirmation=true`

This makes conversion artifact-backed and auditable.
