# Patch Plan & Next Steps

## Current Patch Sets (Committed)

### Patch Set A — Inbound Webhook Enterprise Hardening
- Verify provider signatures (Meta Cloud API HMAC) and reject invalid signatures.
- Resolve tenant via `whatsapp_accounts` mapping (never trust `X-Tenant-ID` for webhooks).
- Enforce idempotency with `webhook_events` unique constraint and message dedupe.
- Persist inbound messages and conversations, and write CRM interactions.

### Patch Set B — Durable Queue + DLQ
- Replace in-process event bus with Celery-backed task.
- Enqueue inbound webhook processing and handle retries with exponential backoff.
- Mark `webhook_events` as `dead_letter` on persistent failure.

### Patch Set C — Tenant Isolation Hardening
- Enable Postgres RLS on tenant-scoped tables and use session-level `app.current_tenant_id`.
- Ensure webhook route bypasses tenant header middleware.
- Add tests covering tenant spoofing and tenant isolation.

## Patch Set 1 (Starting Now): IAM Persistence + Login Hardening

### Goals
- Replace in-memory user storage with SQL-backed persistence.
- Ensure tenant-scoped uniqueness on user email.
- Prepare foundation for role-based authorization in the next iteration.

### Changes Included
- New `users` table with tenant FK and unique `(tenant_id, email)` constraint.
- SQLAlchemy ORM model for `User`.
- SQL repository implementing `UserRepo` interface.
- Container wiring updated to use SQL repo for login/register.
- Add `/auth/signup` to create tenant + user without requiring a tenant header.

### Acceptance Criteria
- Register/login uses SQL repo and persists users across process restarts.
- User email uniqueness enforced per tenant.
- Existing API contracts preserved.
- Signup creates tenant + user and returns a token without requiring `X-Tenant-ID`.

## Next Steps (Detailed)

### Patch Set 2 — Roles & Permissions (RBAC)
1. Add tables: `roles`, `permissions`, `role_permissions`, `memberships`.
2. Implement `RoleRepo` + `MembershipRepo` with tenant scoping.
3. Add route dependencies to enforce permissions (e.g., `crm:write`).
4. Add tests for permission enforcement in CRM/Billing routes.

### Patch Set 3 — Token Hardening
1. Move from custom HMAC token to JWT with `kid`.
2. Add refresh tokens with server-side revocation list or session store.
3. Add rotating signing keys and token TTL policies.
4. Add tests for expiration, rotation, and revocation.

### Patch Set 4 — Provisioning / Tenant Controls
1. Lock `/tenants` route behind admin/system auth or provisioning API key.
2. Add audit logging for tenant creation.
3. Add tests for unauthorized tenant creation attempts.

### Patch Set 5 — Observability
1. Add structured logging with request IDs and tenant IDs.
2. Add metrics and tracing hooks for key workflows (auth, inbound webhooks, queue).
3. Add dashboards/alerts (DLQ size, webhook failures, auth failures).
