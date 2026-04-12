# Assistant Contracts v1 — Handoff / Quote / Consult

This document defines **contract-first** interfaces for the next assistant operational actions in `theone`.

This is **not** a workflow implementation. Persistence, queue orchestration, and lifecycle automation are intentionally deferred.

## Operational context

Existing assistant operational surface (Week 1 foundation):

- `POST /api/chatbot/message`
- `POST /api/chatbot/reset`
- `POST /crm/assistant/prebook`

This v1 spec defines the **next** operational action payloads that `chatbot1` / dashboard can use once endpoints are implemented.

## Common Envelope (v1)

All assistant operational actions use a shared envelope (backend schema `AssistantActionEnvelopeV1`):

| Field | Type | Required | Notes |
|------|------|----------|------|
| `trace_id` | string | yes | Correlation id. Also carried by `X-Trace-Id`. |
| `tenant_id` | UUID | yes | Tenant/workspace boundary. |
| `conversation_id` | UUID \| null | no | Assistant conversation id when known. |
| `session_id` | string \| null | no | Session identifier (may be non-UUID). |
| `customer_id` | UUID \| null | no | Customer id when action is tied to a customer. |
| `source` | enum | yes | One of: `dashboard`, `chatbot1`, `api`, `system`. |
| `actor` | object | yes | `{ type: "staff"|"system"|"customer"|"service", id: UUID|null }` |
| `idempotency_key` | string \| null | no | Safe retry key. Pattern: `^[A-Za-z0-9][A-Za-z0-9:._-]{0,254}$` |
| `meta` | object | no | Low-risk metadata (avoid PII). |

Compatibility guidance:
- Envelope fields are named to match current assistant patterns (`tenant_id`, `conversation_id`, `session_id`, `trace_id`).
- New assistant actions should **inherit** the envelope rather than duplicating fields.

## Common Time Window (v1)

Some contracts reference a reusable time window shape (backend schema `AssistantTimeWindowV1`):

| Field | Type | Required | Notes |
|------|------|----------|------|
| `starts_at` | datetime \| null | no | RFC3339 datetime **with timezone**. |
| `ends_at` | datetime \| null | no | RFC3339 datetime **with timezone**. Requires `starts_at`. |
| `requested_date` | string \| null | no | Local date `"YYYY-MM-DD"` (shape validation only). |
| `requested_time` | string \| null | no | Local time `"HH:MM"` (shape validation only). |
| `timezone` | string \| null | no | IANA timezone name (e.g. `Europe/Lisbon`). |

Validation rules:
- If both `starts_at` and `ends_at` are provided: they must be timezone-aware and `starts_at < ends_at`.
- `ends_at` without `starts_at` is invalid.
- If `starts_at` is not provided, `requested_date` + `requested_time` may be provided to represent a conversational/local intent (timezone interpretation is deferred to the implementing endpoint).

## Handoff contract v1

### Request: `AssistantHandoffRequestInV1`

Required additional fields:
- `reason` (string, 1–500)
- `queue_key` (string, 1–64)
- `summary` (string, 1–2000)

Optional additional fields:
- `priority`: `low | normal | high | urgent` (default: `normal`)
- `context`: object (structured context; avoid PII where possible)
- `requested_sla_minutes`: integer (1…10080)

Example:

```json
{
  "trace_id": "d7c2d4c7d04a4df8b02a2e4c37a1f9c1",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "conversation_id": "22222222-2222-2222-2222-222222222222",
  "session_id": "chatbot-session-123",
  "customer_id": "33333333-3333-3333-3333-333333333333",
  "source": "chatbot1",
  "actor": { "type": "service", "id": null },
  "idempotency_key": "handoff:conv:2222:001",
  "meta": { "surface": "dashboard" },
  "reason": "validation_error",
  "priority": "high",
  "queue_key": "ops.booking",
  "summary": "Cliente pediu agendamento, mas data/hora inválidas repetidamente.",
  "context": { "last_user_message": "quero amanhã 25:99" },
  "requested_sla_minutes": 30
}
```

### Response: `AssistantHandoffResponseOutV1`

Fields:
- `handoff_id` (UUID)
- `status`: `open | accepted | closed | expired`
- `queue_key` (string)
- `accepted_by` (optional object with `actor_type`, `actor_id`, `name`)
- `opened_at`, `updated_at` (RFC3339 datetime)

Deferred / intentionally not modeled:
- queue implementation, assignment rules, operator messaging, SLA enforcement.

## Quote contract v1

### Request: `AssistantQuoteRequestInV1`

Rules:
- `service_ids` must contain at least 1 UUID.
- `location_id` is optional (tenant may have default).
- `requested_window` is optional and uses the common time-window shape.

Example:

```json
{
  "trace_id": "d7c2d4c7d04a4df8b02a2e4c37a1f9c1",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "conversation_id": null,
  "session_id": "chatbot-session-123",
  "customer_id": "33333333-3333-3333-3333-333333333333",
  "source": "chatbot1",
  "actor": { "type": "service", "id": null },
  "idempotency_key": "quote:3333:001",
  "meta": {},
  "service_ids": ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
  "location_id": null,
  "requested_window": {
    "starts_at": null,
    "ends_at": null,
    "requested_date": "2026-04-20",
    "requested_time": "10:00",
    "timezone": "Europe/Lisbon"
  },
  "constraints": {
    "budget_max_cents": 8000,
    "professional_preference": "Maria",
    "extra": {}
  },
  "notes": "Preferência por manhã."
}
```

### Response: `AssistantQuoteResponseOutV1`

Fields:
- `quote_request_id` (UUID)
- `status`: `open | in_review | proposed | accepted | rejected | expired`
- `service_ids`, `location_id`
- `summary` (optional)
- `created_at`, `updated_at`

Deferred:
- actual quote pricing lifecycle, proposals, acceptance workflow.

## Consult contract v1

### Request: `AssistantConsultRequestInV1`

Rules:
- `consult_type` enum: `in_person | phone | video | whatsapp | unspecified`
- `preferred_windows` is optional (max 5), uses the common time-window shape.
- `service_interest` supports both `service_ids[]` and `free_text` fallback.
- `location_preference` supports `location_id` or `free_text`.

Example:

```json
{
  "trace_id": "d7c2d4c7d04a4df8b02a2e4c37a1f9c1",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "conversation_id": "22222222-2222-2222-2222-222222222222",
  "session_id": "chatbot-session-123",
  "customer_id": null,
  "source": "dashboard",
  "actor": { "type": "staff", "id": "44444444-4444-4444-4444-444444444444" },
  "idempotency_key": null,
  "meta": {},
  "consult_type": "whatsapp",
  "service_interest": { "service_ids": [], "free_text": "Avaliar corte e barba" },
  "preferred_windows": [
    { "starts_at": null, "ends_at": null, "requested_date": "2026-04-22", "requested_time": "14:00", "timezone": "Europe/Lisbon" }
  ],
  "location_preference": { "location_id": null, "free_text": "Centro" },
  "notes": "Cliente quer tirar dúvidas antes de marcar.",
  "context": { "channel": "dashboard" }
}
```

### Response: `AssistantConsultResponseOutV1`

Fields:
- `consult_request_id` (UUID)
- `status`: `open | contacting | scheduled | completed | cancelled`
- `consult_type`
- `created_at`, `updated_at`

Deferred:
- scheduling workflow and state transitions beyond the status enum.

## Backend/Frontend alignment

- Backend schemas live under `modules/assistant/contracts/*`.
- Frontend TS types live under `frontend/lib/contracts/assistant.ts`.

Contract versioning:
- These are **v1** contracts. Any breaking changes should ship as a **v2** schema + docs.
