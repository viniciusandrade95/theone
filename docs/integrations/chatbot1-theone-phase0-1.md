# chatbot1 + theone integration (Phase 0/1 status)

## Scope and architecture guardrails

- `theone` remains source of truth for CRM/business entities and booking flows.
- `chatbot1` is used only as orchestration/conversational engine.
- Browser must call `theone` routes only; no direct browser -> `chatbot1` calls.
- Tenant mapping for integration is currently `tenant_id -> client_id` (1:1) and is enforced server-side.

## Backend-facing integration inventory already used by frontend

### Existing covered domains

- **customers**: `/crm/customers`, `/crm/customers/{id}`, interactions sub-routes.
- **appointments**: `/crm/appointments`, `/crm/calendar`, update/cancel/confirmation paths.
- **services**: `/crm/services` CRUD + online bookable flag.
- **booking settings**: `/crm/booking/settings`.
- **locations**: `/crm/locations`, `/crm/locations/default` and location settings under `/crm/settings/location`.
- **availability**: `/public/book/{slug}/availability`.

### Missing/new integration capabilities added in this phase

- **assistant messaging proxy**: `POST /api/chatbot/message`.
- **assistant session reset proxy**: `POST /api/chatbot/reset`.
- **assistant operational endpoint (Release 1)**: `POST /crm/assistant/prebook` (creates a real prebooking/appointment in `theone`).

### Still missing for Phase 2

- **handoff orchestration** (workflow/queue/SLA ownership, domain event hooks).
- **quote request domain endpoint** (no first-class quote aggregate yet).
- **consultation request endpoint/workflow** (needs explicit aggregate + state transitions).
- **tool-level assistant authorization policy matrix** (intent/action permissions by role).

Contracts for the above assistant actions are defined (contract-first) in:
- `docs/contracts/assistant-handoff-quote-consult-v1.md`

## New assistant proxy contract (stable frontend shape)

### POST `/api/chatbot/message`

Request:

```json
{
  "message": "string",
  "conversation_id": "uuid | null",
  "session_id": "string | null",
  "surface": "dashboard",
  "customer_id": "uuid | null"
}
```

Response (normalized):

```json
{
  "conversation_id": "uuid",
  "session_id": "string | null",
  "status": "ok | ...",
  "reply": {
    "text": "string",
    "actions": []
  },
  "intent": "string | null",
  "handoff": {
    "requested": false,
    "reason": null
  },
  "trace_id": "string",
  "client_id": "tenant_id",
  "meta": {
    "source": "chatbot1",
    "raw": {}
  }
}
```

### POST `/api/chatbot/reset`

Request:

```json
{
  "conversation_id": "uuid | null",
  "surface": "dashboard"
}
```

Response:

```json
{
  "ok": true,
  "conversation_id": "uuid",
  "session_id": null,
  "status": "reset",
  "trace_id": "string | null",
  "meta": {
    "source": "chatbot1",
    "raw": {}
  }
}
```

## Persistence implementation

Implemented table: `chatbot_conversation_sessions`.

Fields persisted:
- `conversation_id` (PK)
- `tenant_id`
- `user_id`
- `customer_id` (nullable)
- `client_id`
- `chatbot_session_id` (nullable)
- `surface`
- `status`
- `last_error`
- `created_at`, `updated_at`, `last_message_at`

Uniqueness rule:
- `(tenant_id, user_id, surface)` unique session scope for dashboard assistant usage.

### Release 1 prebooking idempotency

Implemented table: `assistant_prebook_requests`.

Purpose:
- enforce `idempotency_key` for assistant-driven prebooking creation
- store the created `appointment_id` (prebooking reference) for duplicate retries
- keep minimal linkage to `conversation_id`, `session_id` and `trace_id`

## Environment variables

- `CHATBOT_SERVICE_BASE_URL` (server-only, required for live upstream calls).
- `CHATBOT_SERVICE_TIMEOUT_SECONDS` (defaults to `15`).
- `ASSISTANT_CONNECTOR_TOKEN` (server-only shared secret for `chatbot1` -> `theone` connector calls).

## Security and boundary notes

- Authenticated user + tenant context are required for assistant endpoints.
- `X-Trace-Id` is accepted and forwarded upstream.
- If `X-Trace-Id` is missing, `theone` generates a server-side `trace_id` and returns it (also as response header `X-Trace-Id`).
- Upstream credentials/URL remain server-side only.
- WhatsApp integration is intentionally not in scope for these routes.

## Observability baseline (Week 1)

This repo exposes a minimal production-readiness foundation for assistant traffic:

- **Operational surface (official)**:
  - `POST /api/chatbot/message`
  - `POST /api/chatbot/reset`
  - `POST /crm/assistant/prebook`
- **Structured logs**:
  - JSON logs with `event`, `trace_id`, `tenant_id`, `user_id`, `method`, `path`, `status_code`, `duration_ms`.
  - Assistant-specific events include:
    - `assistant_chatbot_request_started` / `assistant_chatbot_request_completed`
    - `assistant_chatbot_upstream_started` / `assistant_chatbot_upstream_completed` / `assistant_chatbot_upstream_failed`
    - `assistant_prebook_created` / `assistant_prebook_conflict` / `assistant_prebook_idempotent_hit`
- **Metrics**:
  - `GET /metrics` (Prometheus text format) does not require `X-Tenant-ID`.
  - Key metrics include `http_requests_total`, `http_request_duration_seconds`, and assistant-specific counters/histograms.

## Release 1: operational prebooking endpoint

### POST `/crm/assistant/prebook`

Auth:
- Either `Authorization: Bearer <staff_jwt>` (dashboard/internal testing), or
- `X-Assistant-Token: <ASSISTANT_CONNECTOR_TOKEN>` (server-to-server from `chatbot1` / TheOneConnector).

Tenant:
- `X-Tenant-ID` header is required.
- Body `tenant_id` must match the tenant header (guardrail).

Request:

```json
{
  "tenant_id": "uuid",
  "conversation_id": "uuid | null",
  "session_id": "string | null",
  "trace_id": "string | null",
  "idempotency_key": "string",
  "customer": {
    "customer_id": "uuid | null",
    "name": "string | null",
    "phone": "string | null",
    "email": "string | null"
  },
  "booking": {
    "service_id": "uuid",
    "location_id": "uuid | null",
    "requested_date": "YYYY-MM-DD | null",
    "requested_time": "HH:MM | null",
    "starts_at": "RFC3339 datetime | null",
    "ends_at": "RFC3339 datetime | null",
    "notes": "string | null"
  },
  "meta": {
    "surface": "dashboard",
    "actor_type": "staff | system",
    "actor_id": "uuid | null",
    "source": "chatbot1"
  }
}
```

Notes:
- If `customer.customer_id` is omitted, `customer.name` + `customer.phone` are required (conservative identity).
- Time window must be future and valid (`starts_at < ends_at`). If `ends_at` is omitted, it is derived from service duration.
- Conflicts return `409` with `{ "error": "APPOINTMENT_OVERLAP", "conflicts": [...] }`.
- A successful prebooking is created as an `appointments` row with `needs_confirmation=true` (no auto-confirm by default).

Success response:

```json
{
  "ok": true,
  "reference": "PB-XXXXXXXX",
  "status": "created | existing",
  "message": "string",
  "trace_id": "string",
  "data": {
    "prebooking_id": "uuid",
    "appointment_id": "uuid",
    "customer_id": "uuid",
    "service_id": "uuid",
    "location_id": "uuid",
    "starts_at": "RFC3339 datetime",
    "ends_at": "RFC3339 datetime",
    "needs_confirmation": true
  }
}
```
