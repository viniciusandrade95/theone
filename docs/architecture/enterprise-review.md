# Enterprise Architecture Review

## CURRENT STATE

### Repository/module map (server)
- **Core**
  - Configuration: `core/config/*` loads env vars into `AppConfig` and provides a singleton accessor.【F:core/config/env.py†L1-L54】【F:core/config/loader.py†L1-L15】
  - Tenancy context: a `ContextVar` holds `tenant_id`, with helper functions for set/clear/require.【F:core/tenancy/context.py†L1-L20】【F:core/tenancy/enforcement.py†L1-L7】
  - Security: HMAC-based token issuing/verification (custom format, not JWT).【F:app/auth_tokens.py†L1-L63】
  - Observability stubs: `core/observability/*` are empty placeholders.【F:core/observability/logging.py†L1-L1】【F:core/observability/metrics.py†L1-L1】【F:core/observability/tracing.py†L1-L1】
  - Errors: typed domain errors mapped to HTTP responses.【F:core/errors/domain.py†L1-L29】【F:core/errors/http.py†L1-L30】
- **Modules (domain-boundaries, “modular monolith” per repo map)**
  - Tenants: `modules/tenants` (domain + repo + service). SQL repo uses `tenants` table.【F:modules/tenants/models/tenant.py†L1-L22】【F:modules/tenants/repo/sql.py†L1-L21】【F:modules/tenants/service/tenant_service.py†L1-L26】
  - IAM: `modules/iam` (domain + in-memory repo + auth service). No SQL repo for users.【F:modules/iam/models/user.py†L1-L36】【F:modules/iam/repo/in_memory.py†L1-L21】【F:modules/iam/service/auth_service.py†L1-L46】
  - CRM: `modules/crm` (customers, interactions, pipeline). SQL repo persists to `customers` and `interactions` tables with tenant scoping in queries.【F:modules/crm/models/customer.py†L1-L76】【F:modules/crm/models/interaction.py†L1-L38】【F:modules/crm/repo/sql.py†L1-L108】
  - Messaging: `modules/messaging` (inbound message parsing + service). Inbound messages are stored as CRM interactions, not as separate message records.【F:modules/messaging/models/inbound.py†L1-L30】【F:modules/messaging/service/inbound_service.py†L1-L27】【F:modules/crm/service/crm_service.py†L52-L70】
  - Billing: `modules/billing` (plan tiers/limits + in-memory subscription repo). Limits enforced in CRM and IAM services only; no usage persistence.【F:modules/billing/models/plans.py†L1-L37】【F:modules/billing/service/billing_service.py†L1-L86】【F:modules/iam/service/auth_service.py†L15-L33】【F:modules/crm/service/crm_service.py†L18-L37】
  - Analytics: `modules/analytics` (summary metrics derived from CRM tables). SQL repo reads CRM tables by tenant.【F:modules/analytics/service/analytics_service.py†L1-L34】【F:modules/analytics/repo/sql.py†L1-L39】
- **HTTP API** (`FastAPI`)
  - App bootstrapping and middleware defined in `app/http/main.py` with a per-request tenancy middleware that reads the tenant header and checks tenant existence except for `/auth/register` and `/tenants` paths.【F:app/http/main.py†L1-L47】
  - Routes:
    - Auth: `/auth/register`, `/auth/login` (tenant header required, token issuance).【F:app/http/routes/auth.py†L1-L47】
    - CRM: `/crm/customers`, `/crm/customers/{id}/interactions`, `/crm/customers/{id}/stage` (require tenant header + user).【F:app/http/routes/crm.py†L1-L48】
    - Messaging: `/messaging/inbound` (enqueues inbound event).【F:app/http/routes/messaging.py†L1-L23】
    - Billing: `/billing/status`, `/billing/plan` (tenant + user).【F:app/http/routes/billing.py†L1-L31】
    - Analytics: `/analytics/summary` (tenant + user).【F:app/http/routes/analytics.py†L1-L25】
    - Tenants: `/tenants` creation (no auth/tenant header requirement).【F:app/http/routes/tenants.py†L1-L22】
- **Async/background processing**
  - In-process `EventBus` with synchronous handler dispatch. An inbound worker handles `MessageReceived` events and calls the inbound service.【F:core/events/bus.py†L1-L18】【F:tasks/workers/messaging/inbound_worker.py†L1-L22】
  - HTTP route uses `BackgroundTasks` to publish to the in-process bus (still same process).【F:app/http/routes/messaging.py†L1-L23】
- **Persistence/DB**
  - SQLAlchemy ORM for tenants/customers/interactions, tables created in Alembic migrations and in test/dev bootstrap if DB URL is `dev`.【F:modules/tenants/models/tenant_orm.py†L1-L15】【F:modules/crm/models/customer_orm.py†L1-L44】【F:modules/crm/models/interaction_orm.py†L1-L39】【F:core/db/session.py†L1-L44】
  - Two Alembic revisions both create `tenants`, `customers`, `interactions` tables (duplicated schema definitions).【F:alembic/versions/5f30581cbf4b_initial_multi_tenant_schema.py†L1-L97】【F:alembic/versions/bef04fb0b750_create_tenants_customers_interactions_.py†L1-L86】

### Tenant scoping (end-to-end)
- Tenant header is required in middleware; tenant id is set on a ContextVar and cleared after request completes.【F:app/http/main.py†L20-L47】【F:core/tenancy/context.py†L1-L20】
- `require_user` validates a bearer token whose payload includes the tenant id, and enforces tenant match vs header context.【F:app/http/deps.py†L23-L44】【F:app/auth_tokens.py†L30-L63】
- Domain services access tenant via `require_tenant_id()`; repos require tenant_id parameters and scope SQL queries by tenant_id where implemented (CRM, analytics).【F:core/tenancy/enforcement.py†L1-L7】【F:modules/crm/repo/sql.py†L24-L60】【F:modules/analytics/repo/sql.py†L14-L39】
- Background worker sets the tenant context from the event before processing.【F:tasks/workers/messaging/inbound_worker.py†L12-L22】

### Authn/Authz model
- Auth: custom HMAC token with `tenant_id`, `user_id`, `exp` claims; no refresh, rotation, or issuer/audience claims.【F:app/auth_tokens.py†L13-L63】
- AuthZ: coarse checks only. CRM/Billing/Analytics routes require authenticated user; `/tenants` is open; `/messaging/inbound` requires only tenant header; there is no RBAC/role model or permission checks. (See routes + IAM service).【F:app/http/routes/tenants.py†L1-L22】【F:app/http/routes/messaging.py†L1-L23】【F:app/http/routes/crm.py†L1-L48】【F:modules/iam/service/auth_service.py†L15-L46】

### Billing model & limit enforcement
- Billing uses in-memory subscription storage. Plans/limits defined in code, with gates for WhatsApp + automations and limits for users/customers/automations.【F:modules/billing/models/plans.py†L1-L37】【F:modules/billing/service/billing_service.py†L1-L86】
- Enforcement in service layer only: `AuthService.register` checks user count; `CrmService.create_customer` checks customers limit; inbound messaging worker checks WhatsApp feature gate.【F:modules/iam/service/auth_service.py†L15-L33】【F:modules/crm/service/crm_service.py†L18-L37】【F:tasks/workers/messaging/inbound_worker.py†L12-L22】

### Messaging model
- Inbound payload is parsed into `InboundMessage` and converted into a CRM interaction of type `whatsapp` (no separate message entity).【F:modules/messaging/models/inbound.py†L1-L30】【F:modules/messaging/service/inbound_service.py†L1-L27】【F:modules/crm/service/crm_service.py†L52-L70】
- No outbound message model, templates, or automation rules; no webhook verification for inbound. There is a config field for `WHATSAPP_WEBHOOK_SECRET` but no usage in code.【F:core/config/env.py†L45-L54】【F:modules/messaging/service/inbound_service.py†L1-L27】

### Background jobs / async processing
- Only in-process event bus + background task; no external queue or retries/DLQ; `tasks/workers/*` includes a single inbound worker and empty schedulers.【F:core/events/bus.py†L1-L18】【F:tasks/workers/messaging/inbound_worker.py†L1-L22】【F:tasks/schedulers/daily.py†L1-L1】

### Observability & security controls
- Observability modules exist but are empty. No logging/tracing/metrics instrumentation in HTTP or services. There is no central audit logging or request ID propagation.【F:core/observability/logging.py†L1-L1】【F:core/observability/metrics.py†L1-L1】【F:core/observability/tracing.py†L1-L1】
- Security controls are limited to basic token validation + tenant header checks; no RBAC, no per-resource authorization, no webhook signature validation, and no DB RLS enforcement. (See security + tenancy + messaging).【F:app/auth_tokens.py†L13-L63】【F:app/http/deps.py†L1-L52】【F:modules/messaging/service/inbound_service.py†L1-L27】【F:core/tenancy/enforcement.py†L1-L7】

---

## TARGET STATE (Enterprise-grade)

### Required domain entities + tables
> Minimal set to support multi-tenant Beauty CRM + WhatsApp automation.

**Tenancy & IAM**
- `tenants` (id, name, status, created_at, billing_customer_id, billing_status)
- `users` (id, tenant_id, email, password_hash, status, created_at, last_login_at)
- `roles` (id, tenant_id, name, description)
- `memberships` (id, tenant_id, user_id, role_id, status)
- `permissions` (id, name, description) + `role_permissions` join table
- `api_keys` (id, tenant_id, name, hashed_secret, scopes, last_used_at)

**CRM**
- `customers` (id, tenant_id, name, phone, email, tags, consent_marketing, stage, created_at)
- `interactions` (id, tenant_id, customer_id, type, payload, created_at)
- `appointments` (id, tenant_id, customer_id, scheduled_at, status, notes)

**Messaging + automation**
- `conversations` (id, tenant_id, channel, customer_id, state, last_message_at)
- `messages` (id, tenant_id, conversation_id, direction, provider, provider_message_id, from_phone, to_phone, body, media, status, sent_at, received_at)
- `message_templates` (id, tenant_id, name, provider_template_id, language, body, variables, status)
- `automation_rules` (id, tenant_id, name, trigger_type, conditions, actions, enabled)
- `automation_runs` (id, tenant_id, rule_id, triggered_by_message_id, status, started_at, completed_at)
- `webhook_events` (id, tenant_id, provider, external_event_id, payload, signature_valid, received_at, processed_at, status)
- `whatsapp_accounts` (id, tenant_id, provider, provider_account_id, phone_number_id, status, created_at)

**Billing + usage**
- `subscriptions` (id, tenant_id, provider, provider_subscription_id, plan_tier, status, started_at, ends_at)
- `usage_records` (id, tenant_id, metric_name, quantity, period_start, period_end, source)
- `plan_limits` (plan_tier, metric_name, limit_value, is_unlimited)

**Ops + audit**
- `audit_log` (id, tenant_id, actor_id, action, target_type, target_id, metadata, created_at)
- `outbox` (id, tenant_id, event_type, payload, status, retries, next_attempt_at, created_at)

### WhatsApp provider integration plan
- **Provider choice:** **Meta Cloud API** (primary) with Twilio fallback for availability.
  - Reasoning: Meta Cloud is canonical, lower per-message costs, and closer to native WhatsApp features; also simplifies webhook data model alignment.
  - Implement provider interface: `MessagingProvider` with `send_message`, `fetch_media`, `verify_webhook`, `normalize_inbound`.
- **Webhook handling:**
  - Verify `X-Hub-Signature-256` (Meta) or Twilio signature; store every webhook payload in `webhook_events` with `external_event_id` dedupe.
  - Enqueue processing job that resolves tenant via provider account mapping and writes `messages`/`conversations`.
- **Outbound:**
  - Template management and message send use provider API; persist provider IDs + status callbacks into `messages` and `webhook_events`.

### Queue/scheduler plan
- **Queue**: Celery or RQ (Python) backed by Redis; Arq also acceptable.
- **Required semantics**
  - Retries with exponential backoff, max attempts; store status in `outbox` or `jobs` table.
  - Idempotency keys for inbound events (`provider_message_id` + `tenant_id`) and outbound (`client_message_id`).
  - DLQ for poison messages; alert on DLQ growth.
- **Workers**
  - `inbound_message_processor` (webhook -> normalize -> dedupe -> persist -> trigger automations)
  - `outbound_message_sender` (send + status updates)
  - `automation_runner` (rules -> actions)
  - `usage_aggregator` (daily/monthly usage records)
- **Scheduler**
  - Daily: usage aggregation + data retention.
  - Monthly: billing reconciliation + plan enforcement.

### Tenant isolation hardening
- Prefer **Postgres RLS** with per-connection `app.current_tenant_id` and policies on all tenant-scoped tables.
- If RLS cannot be used, enforce tenant_id in every query + add automated tests that ensure tenant scoping in repos and in background jobs.
- Enforce tenant IDs through middleware + token claims + service/repo API signatures to prevent bypass.

---

## GAP LIST

> Each gap lists severity, impacted files (or “missing file/table”), impact, and recommended fix.

### a) Security/AuthZ
1. **No RBAC/permissions model** (High)
   - **Files**: missing `roles`, `memberships`, `permissions` tables; API routes have no role checks.【F:app/http/routes/crm.py†L1-L48】【F:app/http/routes/billing.py†L1-L31】
   - **Impact**: all authenticated users can access any action within tenant; cannot enforce least privilege.
   - **Fix**: add role/membership entities, authorization checks in route dependencies and services.
2. **Custom token format without rotation or refresh** (Medium)
   - **Files**: `app/auth_tokens.py` (HMAC tokens).【F:app/auth_tokens.py†L1-L63】
   - **Impact**: no key rotation, revocation, or refresh; difficult to integrate SSO.
   - **Fix**: adopt JWT with `kid`, or session tokens stored server-side; add refresh and revocation.
3. **Tenant creation endpoint is unauthenticated** (High)
   - **Files**: `app/http/routes/tenants.py`.【F:app/http/routes/tenants.py†L1-L22】
   - **Impact**: anonymous creation of tenants enables abuse and namespace squatting.
   - **Fix**: lock behind admin/system auth or provisioning pipeline.

### b) Multi-tenancy isolation (API + DB + background jobs)
1. **No DB-level RLS / hard isolation** (Critical)
   - **Files**: all ORM tables (`tenants`, `customers`, `interactions`) and repos rely on application-level filters only.【F:modules/crm/repo/sql.py†L24-L60】【F:modules/analytics/repo/sql.py†L14-L39】
   - **Impact**: any repo bug or missed filter leaks cross-tenant data.
   - **Fix**: implement Postgres RLS policies + tests; ensure session sets tenant context.
2. **In-memory IAM + Billing storage** (High)
   - **Files**: `modules/iam/repo/in_memory.py`, `modules/billing/repo/in_memory.py`.【F:modules/iam/repo/in_memory.py†L1-L21】【F:modules/billing/repo/in_memory.py†L1-L15】
   - **Impact**: auth/billing data is ephemeral, inconsistent across processes.
   - **Fix**: add SQL repos with tenant scoping; migrate users/subscriptions tables.
3. **Background jobs use in-process EventBus only** (Medium)
   - **Files**: `core/events/bus.py`, `app/http/routes/messaging.py`.【F:core/events/bus.py†L1-L18】【F:app/http/routes/messaging.py†L1-L23】
   - **Impact**: no durable queue, no retries; tenant context only in-memory.
   - **Fix**: introduce persistent queue with tenant metadata stored in job payload.

### c) DB schema/migrations/indexes/constraints
1. **Duplicate Alembic migrations for same tables** (High)
   - **Files**: `alembic/versions/5f30581...`, `alembic/versions/bef04fb...` both create `tenants/customers/interactions`.【F:alembic/versions/5f30581cbf4b_initial_multi_tenant_schema.py†L1-L97】【F:alembic/versions/bef04fb0b750_create_tenants_customers_interactions_.py†L1-L86】
   - **Impact**: migration history conflicts; applying both will fail or corrupt schema.
   - **Fix**: squash or delete superseded migration; align schema + history.
2. **Tests refer to non-existent `content` column** (Medium)
   - **Files**: `tests/unit/test_db_constraints.py` expects `interactions.content`, but schema uses `payload` JSONB only.【F:tests/unit/test_db_constraints.py†L44-L56】【F:alembic/versions/5f30581cbf4b_initial_multi_tenant_schema.py†L65-L83】
   - **Impact**: tests fail or drift; data model ambiguity.
   - **Fix**: update tests and/or schema to match intended model.
3. **Missing indexes for common lookup fields** (Low)
   - **Files**: `customers` (phone/email indexes exist only in first migration), `interactions` (no composite index for tenant+customer in one migration).【F:alembic/versions/5f30581cbf4b_initial_multi_tenant_schema.py†L43-L64】【F:alembic/versions/bef04fb0b750_create_tenants_customers_interactions_.py†L52-L86】
   - **Impact**: slower queries as data grows.
   - **Fix**: add proper unique + composite indexes in canonical migration.

### d) WhatsApp messaging + automation
1. **No webhook signature validation or dedup** (Critical)
   - **Files**: inbound route/service handle payload directly; webhook secret unused.【F:app/http/routes/messaging.py†L1-L23】【F:modules/messaging/service/inbound_service.py†L1-L27】【F:core/config/env.py†L45-L54】
   - **Impact**: spoofed webhooks and replayed messages create false interactions.
   - **Fix**: verify signatures, store `webhook_events` with `external_event_id` unique constraint.
2. **No message storage model (messages/conversations)** (High)
   - **Files**: messages stored as CRM interactions only; no provider IDs.【F:modules/messaging/service/inbound_service.py†L1-L27】【F:modules/crm/service/crm_service.py†L52-L70】
   - **Impact**: cannot reconcile delivery status, templates, or automation state.
   - **Fix**: add `messages`/`conversations` tables and domain models.
3. **No automation rules/runner** (Medium)
   - **Files**: missing `automation_rules`/`automation_runs` models and services.
   - **Impact**: cannot deliver automation features.
   - **Fix**: create automation subsystem, triggered by inbound/outbound events.

### e) Billing + plan limits + usage tracking
1. **No persistent subscriptions/usage tables** (High)
   - **Files**: `modules/billing/repo/in_memory.py` (no SQL repo).【F:modules/billing/repo/in_memory.py†L1-L15】
   - **Impact**: billing resets on restart; cannot enforce enterprise limits or billing provider sync.
   - **Fix**: add DB schema + provider integration for subscription lifecycle.
2. **Usage tracking missing** (Medium)
   - **Files**: missing `usage_records`/`plan_limits` tables.
   - **Impact**: cannot enforce limits reliably or bill per usage.
   - **Fix**: add usage aggregation jobs and storage.

### f) Observability/ops
1. **No logging/metrics/tracing implementation** (High)
   - **Files**: `core/observability/*` empty.【F:core/observability/logging.py†L1-L1】【F:core/observability/metrics.py†L1-L1】【F:core/observability/tracing.py†L1-L1】
   - **Impact**: difficult to detect failures, audit or meet enterprise SLAs.
   - **Fix**: implement structured logging, metrics, tracing middleware.
2. **No audit logging** (Medium)
   - **Files**: missing `audit_log` table/services.
   - **Impact**: compliance gaps for enterprise.
   - **Fix**: add audit pipeline for auth/admin actions.

### g) Testing/CI
1. **Mismatch between tests and schema** (Medium)
   - **Files**: tests expect `interactions.content` column but schema uses `payload`.【F:tests/unit/test_db_constraints.py†L44-L56】【F:modules/crm/models/interaction_orm.py†L1-L39】
   - **Impact**: failing tests or incorrect schema validation.
   - **Fix**: align tests with model or change schema.
2. **No integration tests for multi-tenant isolation** (High)
   - **Files**: missing end-to-end tests verifying tenant scoping on DB and API.
   - **Impact**: cross-tenant access regressions unnoticed.
   - **Fix**: add tests to ensure tenant isolation at repo + API layers.

### h) API design (pagination, idempotency, versioning)
1. **No pagination or filtering** (Medium)
   - **Files**: `GET` endpoints return full lists (e.g., analytics summary computed from all interactions).【F:modules/analytics/service/analytics_service.py†L10-L34】
   - **Impact**: performance issues with large datasets.
   - **Fix**: add pagination parameters and index support.
2. **No idempotency for writes/webhooks** (High)
   - **Files**: inbound messaging accepts payload without dedupe; no idempotency keys for create operations.【F:app/http/routes/messaging.py†L1-L23】【F:modules/messaging/service/inbound_service.py†L1-L27】
   - **Impact**: duplicate messages create repeated interactions.
   - **Fix**: enforce idempotency with unique keys + request IDs.
3. **No API versioning** (Low)
   - **Files**: all routes are unversioned (`/crm`, `/auth`, etc.).【F:app/http/main.py†L40-L47】
   - **Impact**: breaking changes hard to roll out.
   - **Fix**: introduce `/v1` prefix or header-based versioning.

---

## BACKLOG

### Epic 1: Tenant isolation hardening
- **Story 1.1: Add Postgres RLS policies**
  - Task 1.1.1 (L): Create migration to enable RLS on tenant-scoped tables (`customers`, `interactions`, `users`, etc.).
    - Acceptance: RLS enabled, policies require `current_setting('app.current_tenant_id')` match.
    - Tests: SQL integration tests to confirm cross-tenant queries return zero rows.
  - Task 1.1.2 (M): Set `SET LOCAL app.current_tenant_id` in DB session (middleware/SQLAlchemy event).
    - Acceptance: tenant_id is set per request and per job; RLS policies enforced.
    - Tests: unit test for session context setting.
- **Story 1.2: Tenant isolation tests**
  - Task 1.2.1 (M): Add API tests verifying tenant header mismatch returns 401.
    - Acceptance: mismatch blocked in `/crm`, `/billing`.
    - Tests: API tests with multiple tenants.

### Epic 2: IAM + AuthZ foundation
- **Story 2.1: Persisted users + roles**
  - Task 2.1.1 (L): Create users/roles/memberships tables + SQL repos.
    - Acceptance: register/login persists users; roles can be assigned.
    - Tests: CRUD tests for user repo and role checks.
- **Story 2.2: Authorization middleware**
  - Task 2.2.1 (M): Implement role-based dependency to guard routes.
    - Acceptance: endpoints require specific permission.
    - Tests: permission denied tests.

### Epic 3: Messaging platform
- **Story 3.1: Webhook ingestion + dedupe**
  - Task 3.1.1 (M): Add `webhook_events` table with unique `external_event_id`.
    - Acceptance: duplicate webhook returns idempotent response.
    - Tests: webhook dedupe test.
  - Task 3.1.2 (M): Validate webhook signature (Meta Cloud API).
    - Acceptance: invalid signature returns 401; valid signature passes.
    - Tests: signature unit tests.
- **Story 3.2: Messaging data model**
  - Task 3.2.1 (L): Add `messages`/`conversations` tables + repos/services.
    - Acceptance: inbound messages stored with provider IDs; conversation updated.
    - Tests: repo tests for unique provider_message_id per tenant.
- **Story 3.3: Automation rules**
  - Task 3.3.1 (L): Implement automation_rules/automation_runs + engine.
    - Acceptance: inbound message triggers automation actions.
    - Tests: rules engine unit tests.

### Epic 4: Job queue and scheduling
- **Story 4.1: Introduce Celery/RQ workers**
  - Task 4.1.1 (M): Add queue infrastructure and worker to process inbound webhooks.
    - Acceptance: HTTP request enqueues job, worker persists message.
    - Tests: integration test with fake queue.
  - Task 4.1.2 (M): Add DLQ + retry policy.
    - Acceptance: failing jobs retry with backoff; DLQ after max attempts.
    - Tests: retry policy tests.
- **Story 4.2: Usage aggregation scheduler**
  - Task 4.2.1 (M): Implement daily/monthly schedulers.
    - Acceptance: usage records generated per tenant.
    - Tests: scheduler unit tests.

### Epic 5: Billing + usage tracking
- **Story 5.1: Subscription persistence**
  - Task 5.1.1 (L): Add `subscriptions` table and SQL repo; integrate with BillingService.
    - Acceptance: plan changes persist across restarts.
    - Tests: repo tests for get/upsert subscription.
- **Story 5.2: Usage records**
  - Task 5.2.1 (M): Add `usage_records` and `plan_limits` tables.
    - Acceptance: limits enforced based on usage records.
    - Tests: usage calculations.

### Epic 6: Observability
- **Story 6.1: Logging/metrics/tracing**
  - Task 6.1.1 (M): Implement request logging + correlation IDs.
    - Acceptance: logs include tenant_id + request_id.
    - Tests: logging middleware tests.
  - Task 6.1.2 (M): Add metrics + tracing exporters.
    - Acceptance: metrics endpoints expose request counts + latencies.
    - Tests: smoke tests for metrics endpoint.

---

## TOP 3 PATCH PLANS

> Concrete proposals for the highest-risk gaps.

### 1) Tenant isolation hardening (RLS + guardrails)
**Goal:** ensure DB-level isolation.

**Steps (migration + code):**
1. Create Alembic migration to enable RLS on tenant-scoped tables:
   ```sql
   ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation ON customers
     USING (tenant_id::text = current_setting('app.current_tenant_id'));
   ```
2. Add SQLAlchemy session event to set tenant context when a request/job starts:
   ```python
   session.execute(text("SET LOCAL app.current_tenant_id = :tenant"), {"tenant": tenant_id})
   ```
3. Add tests that attempt cross-tenant access in repos and assert zero rows returned.

**Files to add/change:**
- `alembic/versions/<new>_enable_rls.py`
- `core/db/session.py` (set session variable)
- `tests/integration/test_rls.py`

### 2) Messaging data model + webhook dedupe + signature verification
**Goal:** make inbound webhook secure and idempotent.

**Diff-style sketch:**
```diff
+ op.create_table(
+   "webhook_events",
+   sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
+   sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
+   sa.Column("provider", sa.String(), nullable=False),
+   sa.Column("external_event_id", sa.String(), nullable=False),
+   sa.Column("payload", postgresql.JSONB(), nullable=False),
+   sa.Column("signature_valid", sa.Boolean(), nullable=False),
+   sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
+   sa.UniqueConstraint("tenant_id", "provider", "external_event_id")
+ )
```
```diff
+ def verify_webhook(request: Request) -> None:
+     signature = request.headers.get("X-Hub-Signature-256")
+     # compute HMAC and compare against configured secret
```
- Create `MessagingProvider` interface and `MetaCloudProvider` implementation that normalizes inbound payloads.
- Store normalized inbound messages into `messages` table with unique constraint on (`tenant_id`, `provider_message_id`).

**Files to add/change:**
- `modules/messaging/models/message.py`, `modules/messaging/repo/sql.py`, `modules/messaging/service/inbound_service.py`
- `app/http/routes/messaging.py` (signature check + dedupe)
- `alembic/versions/<new>_messaging_models.py`

### 3) Job queue for messaging/automation off request path
**Goal:** durable processing with retries.

**Steps:**
1. Add Redis + Celery (or RQ) config and worker entrypoint.
2. Replace in-process `EventBus` with queue task for inbound processing:
   ```python
   @router.post("/inbound")
   def inbound(...):
       enqueue_inbound_webhook(tenant_id, payload)
       return {"status": "accepted"}
   ```
3. Worker validates signature, dedupes webhook event, persists messages, triggers automations.
4. Add DLQ and retry policy for transient failures.

**Files to add/change:**
- `tasks/workers/messaging/inbound_worker.py` (queue task signature)
- `tasks/queue.py` (new)
- `docker-compose.yml` (add Redis)

