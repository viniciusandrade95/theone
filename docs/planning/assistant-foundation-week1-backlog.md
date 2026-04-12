# Assistant Foundation — Week 1 Backlog

Date: 2026-04-12
Owner suggestion: PM + Backend
Status: proposed
Branch: `pm/assistant-foundation-week1-backlog`

## Goal

Deliver the mandatory foundation for the assistant in 1 week, with the smallest possible implementation that still gives production-grade visibility, governance, and tenant safety.

This sprint is **not** a feature sprint. It is a **foundation sprint** for:
- observability baseline
- audit trail for assistant actions
- multitenancy review and hardening
- contract-first definitions for handoff, quote and consult

## Why this sprint exists

The repository already contains assistant/chatbot proxy endpoints, assistant prebooking logic, booking, outbound, audit helpers, and tenant context plumbing. However, the current system still has important weaknesses in observability, route consistency, tenant enforcement, and contract governance.

## Scope

### In scope
- baseline logs + `trace_id` + minimum assistant metrics
- audit trail for assistant actions
- multitenancy review for assistant, booking, and outbound
- contract definitions for handoff, quote, and consult
- tests for the new guardrails
- lightweight documentation update

### Out of scope
- full handoff orchestration workflow
- full quote aggregate implementation
- full consultation workflow/state machine
- advanced distributed tracing platform rollout
- role matrix redesign for the whole product

---

## Architecture notes from current repo state

### Assistant-related runtime surfaces
- `POST /api/chatbot/message`
- `POST /api/chatbot/reset`
- `POST /crm/assistant/prebook`

### Existing strengths to reuse
- `X-Trace-Id` already exists in chatbot and prebook flows
- chatbot upstream client already forwards `X-Trace-Id`
- `audit_log` model and `record_audit_log()` already exist
- appointment repo already writes audit events
- DB session already sets `app.current_tenant_id` for Postgres

### Current risks that must be fixed in this sprint
1. `assistant_prebook` route must be treated as part of the assistant governance surface.
2. `chatbot` session lookup by `conversation_id` is too permissive unless constrained by tenant/user scope.
3. `core/observability/*` is still empty.
4. tenant existence check in HTTP middleware is commented out.
5. tenant header handling is not fully normalized across middleware and deps.
6. outbound actions do not yet benefit from the same audit rigor already used in appointments.

---

## Delivery plan

### PR 1 — Assistant surface alignment + observability baseline

#### Ticket A1 — Mount and normalize assistant routes
**Type:** backend hardening
**Priority:** P0

**Problem**
Assistant behavior is split across chatbot proxy and prebook. Governance work must cover both explicitly.

**Tasks**
- Ensure `/crm/assistant/prebook` is mounted in app bootstrap.
- Treat `chatbot_message`, `chatbot_reset`, and `assistant_prebook` as the official assistant backend surface.
- Normalize response `trace_id` behavior across all assistant endpoints.

**Files impacted**
- `app/http/main.py`
- `app/http/routes/assistant.py`
- `app/http/routes/assistant_prebook.py`
- `app/http/routes/chatbot.py`
- `docs/integrations/chatbot1-theone-phase0-1.md`

**Acceptance criteria**
- All three assistant endpoints are reachable and documented.
- Every assistant response includes a `trace_id`.
- Missing incoming `X-Trace-Id` generates a server-side trace id.

**Tests**
- API tests for mounted route reachability
- API tests for generated `trace_id`

---

#### Ticket A2 — Replace prebook auth with dual-mode assistant auth
**Type:** backend security/governance
**Priority:** P0

**Problem**
The documented contract says assistant prebook accepts either Bearer staff auth or assistant connector auth.

**Tasks**
- Replace strict `require_assistant_token` dependency with `require_user_or_assistant_connector`.
- Persist/propagate actor mode (`user` vs `assistant_connector`) into request handling and audit metadata.

**Files impacted**
- `app/http/deps.py`
- `app/http/routes/assistant_prebook.py`
- `docs/integrations/chatbot1-theone-phase0-1.md`

**Acceptance criteria**
- Staff bearer token can call prebook.
- Assistant shared secret can call prebook.
- Audit metadata differentiates actor mode.

**Tests**
- API test: Bearer accepted
- API test: assistant token accepted
- API test: invalid token rejected

---

#### Ticket A3 — Structured logging baseline
**Type:** observability
**Priority:** P0

**Problem**
The repo exposes `LOG_LEVEL` but central observability modules are empty.

**Tasks**
- Implement structured JSON logging helpers.
- Add HTTP middleware logging request start/end with:
  - `trace_id`
  - `tenant_id`
  - `user_id`
  - `method`
  - `path`
  - `status_code`
  - `duration_ms`
- Add assistant-specific log events for:
  - chatbot request start/end
  - chatbot upstream error
  - prebook created/conflict/idempotent hit

**Files impacted**
- `core/observability/logging.py`
- `app/http/main.py`
- `app/http/routes/chatbot.py`
- `app/http/routes/assistant_prebook.py`
- `modules/chatbot/service/chatbot_client.py`

**Acceptance criteria**
- Logs are structured and machine-readable.
- Every assistant request can be correlated by `trace_id`.
- Upstream chatbot failures are visible in logs with latency and outcome.

**Tests**
- Middleware/unit tests for trace propagation
- Log capture tests for assistant endpoints

---

#### Ticket A4 — Metrics baseline for assistant
**Type:** observability
**Priority:** P1

**Problem**
There is no metrics baseline for assistant traffic and outcome.

**Tasks**
- Add Prometheus-style metrics endpoint.
- Record minimum metrics:
  - `http_requests_total{route,method,status}`
  - `http_request_duration_seconds{route,method}`
  - `assistant_requests_total{surface,outcome}`
  - `assistant_request_duration_seconds{surface}`
  - `assistant_chatbot_upstream_requests_total{outcome}`
  - `assistant_chatbot_upstream_duration_seconds`
  - `assistant_prebook_total{status}`
  - `outbound_send_total{status,channel,type}`

**Files impacted**
- `core/observability/metrics.py`
- `app/http/main.py`
- `app/http/routes/chatbot.py`
- `app/http/routes/assistant_prebook.py`
- `app/http/routes/outbound.py`

**Acceptance criteria**
- `/metrics` endpoint is exposed.
- Assistant request count, latency and outcomes are visible.
- Outbound send success/failure is counted.

**Tests**
- Smoke test for `/metrics`
- Counter increments for assistant requests

---

### PR 2 — Audit trail expansion + multitenancy hardening

#### Ticket B1 — Expand audit log schema for assistant traceability
**Type:** audit/governance
**Priority:** P0

**Problem**
Existing audit log is useful, but too narrow for assistant investigations.

**Tasks**
- Add migration to extend `audit_log` with:
  - `trace_id` (nullable string)
  - `metadata` (JSONB/JSON)
  - optionally `conversation_id` and `session_id` if judged low-risk and useful
- Keep current `before`/`after` snapshots.

**Files impacted**
- `modules/audit/models/audit_log_orm.py`
- `alembic/versions/<new>_expand_audit_log_for_assistant.py`

**Acceptance criteria**
- Audit log supports assistant correlation by `trace_id`.
- Existing audit writes remain backwards compatible.

**Tests**
- Migration test
- Model insert/read test

---

#### Ticket B2 — Audit assistant actions end to end
**Type:** audit/governance
**Priority:** P0

**Problem**
Assistant actions are not consistently recorded in the central audit trail.

**Tasks**
- Write audit records for:
  - `assistant.chatbot_message_requested`
  - `assistant.chatbot_message_failed`
  - `assistant.chatbot_reset`
  - `assistant.prebook_requested`
  - `assistant.prebook_created`
  - `assistant.prebook_conflict`
  - `assistant.prebook_idempotent_hit`
- Include actor info, trace_id, conversation/session ids when available.

**Files impacted**
- `app/http/routes/chatbot.py`
- `app/http/routes/assistant_prebook.py`
- optionally audit helper wrapper in `modules/audit/logging.py`

**Acceptance criteria**
- Assistant actions create searchable audit rows.
- Failures and idempotent hits are visible, not only successful creates.

**Tests**
- API tests asserting audit rows after chatbot/prebook actions

---

#### Ticket B3 — Extend audit trail to booking settings and outbound actions
**Type:** audit/governance
**Priority:** P1

**Problem**
Appointments already write audit rows, but booking settings and outbound actions do not have equivalent rigor.

**Tasks**
- Audit `booking settings updated`.
- Audit outbound template create/update/delete.
- Audit outbound message send/fail/resend.

**Files impacted**
- `app/http/routes/booking.py`
- `modules/tenants/repo/booking_settings_sql.py`
- `app/http/routes/outbound.py`
- `modules/messaging/repo/outbound_sql.py`

**Acceptance criteria**
- Booking and outbound have central audit visibility.
- Audit rows include tenant, actor and trace context when available.

**Tests**
- API tests for booking settings audit row
- API tests for outbound send audit row

---

#### Ticket B4 — Re-enable tenant existence validation in middleware
**Type:** multitenancy hardening
**Priority:** P0

**Problem**
Tenant existence validation is currently commented out in middleware.

**Tasks**
- Re-enable `tenant_service.get_or_fail(tenant_id)` in tenancy middleware.
- Preserve current public path exceptions intentionally.
- Document allowed bypass routes explicitly.

**Files impacted**
- `app/http/main.py`

**Acceptance criteria**
- Nonexistent tenant header is rejected before protected handlers run.
- Public routes still behave correctly.

**Tests**
- API test: invalid tenant rejected
- API test: public booking still works

---

#### Ticket B5 — Normalize tenant header handling
**Type:** multitenancy hardening
**Priority:** P1

**Problem**
Middleware honors configurable `TENANT_HEADER`, but dependencies/OpenAPI still lean on hardcoded `X-Tenant-ID` behavior.

**Tasks**
- Make tenant dependency reflect configured tenant header behavior consistently.
- Keep OpenAPI accurate enough for current deployment choice.
- Remove silent drift between middleware, deps, and clients.

**Files impacted**
- `app/http/deps.py`
- `app/http/main.py`
- `frontend/lib/api.ts` (if needed)
- docs where tenant header is described

**Acceptance criteria**
- Tenant header behavior is consistent across runtime and docs.
- No route accepts a different effective tenant header than documented.

**Tests**
- Dependency/middleware tests for configured tenant header

---

#### Ticket B6 — Constrain chatbot conversation lookup by tenant and user scope
**Type:** multitenancy hardening
**Priority:** P0

**Problem**
Conversation lookup by `conversation_id` must not permit cross-tenant or cross-user reuse.

**Tasks**
- Update `ChatbotSessionRepo.get_by_conversation_id()` and `get_or_create()` logic to enforce tenant/user scope.
- Reject mismatched `conversation_id` usage.
- Audit failed/mismatched reuse attempts if practical.

**Files impacted**
- `modules/chatbot/repo/session_repo.py`
- `app/http/routes/chatbot.py`

**Acceptance criteria**
- A conversation id created under one tenant/user cannot be reused by another.
- Same tenant/user still gets normal resume behavior.

**Tests**
- API test: tenant A cannot use tenant B conversation id
- API test: user A cannot reuse user B conversation id in same tenant if that is product policy

---

#### Ticket B7 — Execute focused multitenancy review for assistant, booking, outbound
**Type:** review + hardening
**Priority:** P0

**Problem**
The explicit ask is a multitenancy review across assistant, booking and outbound, not just isolated fixes.

**Tasks**
- Produce a short review matrix covering each route:
  - route
  - auth mode
  - tenant source
  - guardrail(s)
  - repo/entity scoping method
  - current risk
  - required fix
- Include public booking routes in the review, not only authenticated booking settings.
- Confirm outbound uses tenant-scoped reads/writes across templates/messages/customers/appointments.

**Files impacted**
- `docs/planning/assistant-foundation-week1-backlog.md`
- optionally a new `docs/audit/assistant-booking-outbound-multitenancy-review.md`

**Acceptance criteria**
- Every in-scope route has an explicit tenant strategy documented.
- Review identifies residual risk and whether it is fixed now or deferred.

**Tests**
- Cross-tenant API tests for representative flows

---

### PR 3 — Contract-first definitions for handoff, quote and consult

#### Ticket C1 — Define common assistant action envelope
**Type:** contracts
**Priority:** P0

**Problem**
New assistant capabilities need a stable, shared shape before workflow implementation begins.

**Tasks**
- Define a common envelope for assistant operational actions with:
  - `trace_id`
  - `tenant_id`
  - `conversation_id`
  - `session_id`
  - `customer_id`
  - `source`
  - `actor`
  - `idempotency_key`
  - `meta`
- Implement as backend Pydantic schema and frontend TS contract.

**Files impacted**
- `modules/assistant/contracts/common.py`
- `frontend/lib/contracts/assistant.ts`
- `docs/contracts/assistant-handoff-quote-consult-v1.md`

**Acceptance criteria**
- Backend and frontend share the same field semantics.
- Envelope is versioned and documented.

**Tests**
- Schema validation tests
- Contract snapshot tests if available

---

#### Ticket C2 — Define handoff contract v1
**Type:** contracts
**Priority:** P0

**Problem**
Handoff is called out in existing docs as still missing.

**Tasks**
- Define request/response contract for handoff.
- Minimum fields:
  - `reason`
  - `priority`
  - `queue_key`
  - `summary`
  - `context`
  - `requested_sla_minutes`
- Define response fields:
  - `handoff_id`
  - `status`
  - `queue_key`
  - `accepted_by`
  - `opened_at`

**Files impacted**
- `modules/assistant/contracts/handoff.py`
- `frontend/lib/contracts/assistant.ts`
- `docs/contracts/assistant-handoff-quote-consult-v1.md`

**Acceptance criteria**
- Contract is explicit enough for frontend and future orchestration.
- OpenAPI/docs are understandable without reading source code.

**Tests**
- Validation tests for required/optional fields

---

#### Ticket C3 — Define quote contract v1
**Type:** contracts
**Priority:** P0

**Problem**
Quote requests do not yet have a first-class contract or aggregate.

**Tasks**
- Define request/response contract for quote.
- Minimum fields:
  - `service_ids[]`
  - `location_id`
  - `constraints`
  - `notes`
  - `requested_window`
- Define status model:
  - `open`
  - `in_review`
  - `proposed`
  - `accepted`
  - `rejected`
  - `expired`

**Files impacted**
- `modules/assistant/contracts/quote.py`
- `frontend/lib/contracts/assistant.ts`
- `docs/contracts/assistant-handoff-quote-consult-v1.md`

**Acceptance criteria**
- Quote request shape is stable and documented.
- Future aggregate implementation can adopt the same public contract.

**Tests**
- Validation tests

---

#### Ticket C4 — Define consult contract v1
**Type:** contracts
**Priority:** P0

**Problem**
Consultation requests are still undefined at domain contract level.

**Tasks**
- Define request/response contract for consult.
- Minimum fields:
  - `consult_type`
  - `service_interest`
  - `preferred_windows[]`
  - `location_preference`
  - `notes`
- Define status model:
  - `open`
  - `contacting`
  - `scheduled`
  - `completed`
  - `cancelled`

**Files impacted**
- `modules/assistant/contracts/consult.py`
- `frontend/lib/contracts/assistant.ts`
- `docs/contracts/assistant-handoff-quote-consult-v1.md`

**Acceptance criteria**
- Consult request shape is stable and documented.
- Contract is enough to unblock UI and downstream design.

**Tests**
- Validation tests

---

## Recommended execution order

### Day 1
- A1 route alignment
- A2 dual-mode prebook auth
- B4 tenant existence validation
- B6 chatbot conversation scoping

### Day 2
- A3 structured logging
- trace propagation cleanup
- response header standardization

### Day 3
- A4 metrics baseline
- smoke tests for `/metrics`
- assistant/outbound counters

### Day 4
- B1 audit schema expansion
- B2 assistant audit events
- B3 booking/outbound audit events

### Day 5
- B7 multitenancy review doc
- C1/C2/C3/C4 contract definitions
- final cleanup, docs and QA

---

## Definition of done

This sprint is done only when all of the following are true:

1. All assistant endpoints return or propagate a usable `trace_id`.
2. Logs allow correlation by `trace_id`, tenant and actor.
3. `/metrics` exposes assistant baseline counters and latency metrics.
4. `audit_log` captures assistant actions and relevant booking/outbound side effects.
5. Tenant existence validation is active again for protected routes.
6. Chatbot conversation reuse is tenant-safe.
7. A written multitenancy review exists for assistant, booking and outbound.
8. Handoff, quote and consult contracts exist as versioned schemas/docs.
9. Automated tests cover the key new guardrails.

---

## Suggested QA checklist

- Send chatbot message with and without `X-Trace-Id`
- Reset chatbot session and confirm trace visibility
- Create assistant prebook with Bearer auth
- Create assistant prebook with assistant connector token
- Retry same prebook idempotency key and verify audit/log behavior
- Trigger appointment conflict and verify metrics + audit + logs
- Update booking settings and verify audit row
- Send outbound message and verify audit + metrics
- Attempt cross-tenant `conversation_id` reuse and confirm rejection
- Call protected route with nonexistent tenant and confirm rejection

---

## Risks and guardrails

### Risks
- touching middleware can break public routes if bypasses are not preserved
- audit schema expansion can create noisy writes if event taxonomy is vague
- metrics cardinality can explode if labels are too dynamic

### Guardrails
- keep metrics labels low-cardinality
- never use customer id / conversation id as metric labels
- keep audit event names explicit and finite
- preserve public booking behavior while hardening protected routes

---

## Post-sprint follow-up (not part of this week)
- assistant authorization policy matrix by intent/action
- actual handoff queue and SLA ownership workflow
- quote aggregate and lifecycle persistence
- consult workflow and operational UI
- richer distributed tracing / OTel rollout
