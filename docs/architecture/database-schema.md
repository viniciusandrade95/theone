# Database Schema (Entities & Tables)

This document describes the **current** database schema used by the CRM SaaS multi-tenant backend.

Sources of truth:
- **PostgreSQL**: `alembic/versions/*.py` migrations are the canonical schema history.
- **SQLite dev/test** (`DATABASE_URL=dev`): schema is created from SQLAlchemy metadata in `core/db/session.py` via `Base.metadata.create_all(...)`.

---

## Runtime Database Choice
- `DATABASE_URL=dev` → SQLite in-memory (`sqlite+pysqlite:///:memory:`)
- Any other `DATABASE_URL` (e.g. `postgresql+psycopg://...`) → PostgreSQL

---

## Multi-Tenancy & RLS
In PostgreSQL, tenant isolation relies on Row Level Security (RLS) + a per-request setting:

- Application sets `app.current_tenant_id` using `set_config('app.current_tenant_id', :tenant_id, true)` in `core/db/session.py`.
- RLS policies typically compare `tenant_id` to `current_setting('app.current_tenant_id', true)::uuid`.

### RLS status by table
RLS enabled (via migrations):
- `customers`, `interactions`
- `services`, `appointments`, `locations`
- `tenant_settings`
- `whatsapp_accounts`, `webhook_events`, `conversations`, `messages`
- `message_templates`, `outbound_messages`
- `audit_log`

Special cases:
- `booking_settings`: **no RLS** (public slug lookup needs to work without a tenant header / tenant context).
- `users`: RLS was created and later explicitly **disabled** (`alembic/versions/347b45647e1f_disable_rls_on_users.py`).

---

## Entity Relationship Map (Text Diagram)

Legend:
- `1 ──< N` means one-to-many
- `1 ── 1` means one-to-one
- `(nullable)` indicates optional FK

```
tenants 1 ──< customers 1 ──< interactions
tenants 1 ──< customers 1 ──< conversations 1 ──< messages

tenants 1 ──< locations 1 ──< appointments >── 1 customers
tenants 1 ──< services  1 ──< appointments (service_id nullable)

tenants 1 ── 1 tenant_settings
tenants 1 ── 1 booking_settings

tenants 1 ──< users
tenants 1 ──< whatsapp_accounts
tenants 1 ──< webhook_events

tenants 1 ──< message_templates 1 ──< outbound_messages (template_id nullable)
tenants 1 ──< outbound_messages (customer_id required, appointment_id nullable)

tenants 1 ──< audit_log
```

---

## Table Reference

### `tenants`
Model: `modules/tenants/models/tenant_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `name` (string, not null)
  - `status` (string, not null, default `"active"`)
  - `created_at` (timestamptz, default `now()`)

---

### `tenant_settings`
Model: `modules/tenants/models/tenant_settings_orm.py`

- Keys:
  - `tenant_id` (UUID, PK, FK → `tenants.id` ON DELETE CASCADE)
- Columns:
  - `business_name` (string(255), null)
  - `default_timezone` (string(120), not null, default `"UTC"`)
  - `currency` (string(12), not null, default `"USD"`)
  - `calendar_default_view` (string(16), not null, default `"week"`)
  - `default_location_id` (UUID, FK → `locations.id` ON DELETE SET NULL, null)
  - `primary_color` (string(32), null)
  - `logo_url` (string(1024), null)
  - `created_at`, `updated_at` (timestamptz)
- RLS:
  - Enabled (policy: `tenant_isolation_tenant_settings`)

---

### `booking_settings`
Model: `modules/tenants/models/booking_settings_orm.py`

- Keys:
  - `tenant_id` (UUID, PK, FK → `tenants.id` ON DELETE CASCADE)
- Columns:
  - `booking_enabled` (bool, not null, default `false`)
  - `booking_slug` (string(80), null, **unique**)
  - `public_business_name` (string(255), null)
  - `public_contact_phone` (string(40), null)
  - `public_contact_email` (string(255), null)
  - `min_booking_notice_minutes` (int, not null, default `60`)
  - `max_booking_notice_days` (int, not null, default `90`)
  - `auto_confirm_bookings` (bool, not null, default `true`)
  - `created_at`, `updated_at` (timestamptz)
- Indexes / constraints:
  - Unique index on `booking_slug` (`ux_booking_settings_slug` in migration)
- RLS:
  - **Disabled** (required for public slug lookup)

---

### `users`
Model: `modules/iam/models/user_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `email` (string, not null)
  - `password_hash` (string, not null)
  - `created_at` (timestamptz)
- Constraints:
  - Unique: (`tenant_id`, `email`) (`uq_users_tenant_email`)
- RLS:
  - Explicitly **disabled** in Postgres (migration `347b45647e1f_disable_rls_on_users.py`)

---

### `customers`
Model: `modules/crm/models/customer_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `name` (string, not null)
  - `phone` (string, null)
  - `email` (string, null)
  - `tags` (JSON/ARRAY(string); in Postgres it is stored as `ARRAY(text)` in the initial migration)
  - `consent_marketing` (bool, default `false`)
  - `consent_marketing_at` (timestamptz, null)
  - `stage` (string, not null)
  - `created_at` (timestamptz)
  - `deleted_at` (timestamptz, null) — soft delete
- Constraints:
  - Unique per tenant (partial, only when not null):
    - (`tenant_id`, `phone`)
    - (`tenant_id`, `email`)
- RLS:
  - Enabled

---

### `interactions`
Model: `modules/crm/models/interaction_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `customer_id` (UUID, FK → `customers.id` ON DELETE CASCADE)
  - `type` (string, not null)
  - `payload` (JSON/JSONB, not null)
  - `created_at` (timestamptz)
- RLS:
  - Enabled

---

### `locations`
Model: `modules/crm/models/location_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `name` (string(120), not null)
  - `timezone` (string(120), not null)
  - `address_line1`, `address_line2`, `city`, `postcode`, `country` (nullable)
  - `phone`, `email` (nullable)
  - `is_active` (bool, not null, default `true`)
  - `hours_json` (JSON/JSONB, null)
  - `allow_overlaps` (bool, not null, default `false`)
  - `created_at`, `updated_at` (timestamptz)
  - `deleted_at` (timestamptz, null) — soft delete
- Indexes (migration `9f3f14db74d0...`):
  - `ix_locations_tenant_active` (`tenant_id`, `is_active`)
  - `ix_locations_tenant_name` (`tenant_id`, `name`)
  - `ix_locations_tenant_deleted` (`tenant_id`, `deleted_at`)
- RLS:
  - Enabled (policy: `tenant_isolation_locations`)

---

### `services`
Model: `modules/crm/models/service_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `name` (string, not null)
  - `price_cents` (int, not null)
  - `duration_minutes` (int, not null)
  - `is_active` (bool, not null, default `true`)
  - `is_bookable_online` (bool, not null, default `false`)
  - `created_at` (timestamptz)
  - `deleted_at` (timestamptz, null) — soft delete
- Indexes (migrations):
  - `ix_services_tenant_name` (`tenant_id`, `name`)
  - `ix_services_tenant_active` (`tenant_id`, `is_active`)
  - `ix_services_tenant_bookable_online` (`tenant_id`, `is_bookable_online`)
  - `ix_services_tenant_deleted` (`tenant_id`, `deleted_at`)
- RLS:
  - Enabled (policy: `services_tenant_isolation`)

---

### `appointments`
Model: `modules/crm/models/appointment_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `customer_id` (UUID, FK → `customers.id` ON DELETE CASCADE)
  - `service_id` (UUID, FK → `services.id` ON DELETE SET NULL, null)
  - `location_id` (UUID, FK → `locations.id` ON DELETE RESTRICT)
  - `starts_at` (timestamptz, not null)
  - `ends_at` (timestamptz, not null)
  - `status` (string, not null, default `"booked"`)
  - `needs_confirmation` (bool, not null, default `false`)
  - `cancelled_reason` (text, null)
  - `status_updated_at` (timestamptz, not null, default `now()`)
  - `notes` (text, null)
  - `created_by_user_id` (UUID, null)
  - `updated_by_user_id` (UUID, null)
  - `created_at` (timestamptz)
  - `deleted_at` (timestamptz, null) — soft delete
- Indexes (migrations):
  - `ix_appointments_tenant_starts` (`tenant_id`, `starts_at`)
  - `ix_appointments_customer` (`tenant_id`, `customer_id`)
  - `ix_appointments_tenant_location_starts` (`tenant_id`, `location_id`, `starts_at`)
  - `ix_appointments_tenant_needs_confirmation` (`tenant_id`, `needs_confirmation`)
  - `ix_appointments_tenant_deleted` (`tenant_id`, `deleted_at`)
- RLS:
  - Enabled (policy: `appointments_tenant_isolation`)
- Domain notes:
  - Allowed statuses enforced in repo layer: `booked`, `completed`, `cancelled`, `no_show` (`modules/crm/repo_appointments.py`).

---

### `whatsapp_accounts`
Model: `modules/messaging/models/whatsapp_account_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `provider` (string, not null)
  - `phone_number_id` (string, not null)
  - `status` (string, not null, default `"active"`)
  - `created_at` (timestamptz)
- Constraints:
  - Unique: (`provider`, `phone_number_id`) (`uq_whatsapp_accounts_provider_phone`)
- RLS:
  - Enabled

---

### `webhook_events`
Model: `modules/messaging/models/webhook_event_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `provider` (string, not null)
  - `external_event_id` (string, not null)
  - `payload` (JSON/JSONB, not null)
  - `signature_valid` (bool, not null)
  - `status` (string, not null, default `"received"`)
  - `received_at` (timestamptz)
  - `processed_at` (timestamptz, null)
- Constraints:
  - Unique: (`tenant_id`, `provider`, `external_event_id`)
- RLS:
  - Enabled

---

### `conversations`
Model: `modules/messaging/models/conversation_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `customer_id` (UUID, FK → `customers.id` ON DELETE CASCADE)
  - `channel` (string, not null)
  - `state` (string, not null, default `"open"`)
  - `last_message_at` (timestamptz, not null, default `now()`)
- Constraints:
  - Unique: (`tenant_id`, `customer_id`, `channel`) (`uq_conversations_tenant_customer_channel`)
- RLS:
  - Enabled

---

### `messages`
Model: `modules/messaging/models/message_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `conversation_id` (UUID, FK → `conversations.id` ON DELETE CASCADE)
  - `direction` (string, not null)
  - `provider` (string, not null)
  - `provider_message_id` (string, not null)
  - `from_phone` (string, not null)
  - `to_phone` (string, null)
  - `body` (string, not null)
  - `status` (string, not null, default `"received"`)
  - `received_at` (timestamptz, null)
  - `sent_at` (timestamptz, null)
  - `created_at` (timestamptz)
- Constraints:
  - Unique: (`tenant_id`, `provider_message_id`) (`uq_messages_tenant_provider_message`)
- RLS:
  - Enabled

---

### `message_templates`
Model: `modules/messaging/models/message_template_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `name` (string(120), not null)
  - `type` (string(64), not null)
  - `channel` (string(32), not null, default `"whatsapp"`)
  - `body` (text, not null)
  - `is_active` (bool, not null, default `true`)
  - `created_at`, `updated_at` (timestamptz)
- Indexes (migration `b0c2d8e8f9a0...`):
  - `ix_message_templates_tenant_type` (`tenant_id`, `type`)
  - `ix_message_templates_tenant_active` (`tenant_id`, `is_active`)
- RLS:
  - Enabled (policy: `tenant_isolation_message_templates`)

---

### `outbound_messages`
Model: `modules/messaging/models/outbound_message_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `customer_id` (UUID, FK → `customers.id` ON DELETE CASCADE)
  - `appointment_id` (UUID, FK → `appointments.id` ON DELETE SET NULL, null)
  - `template_id` (UUID, FK → `message_templates.id` ON DELETE SET NULL, null)
  - `type` (string(64), not null)
  - `channel` (string(32), not null)
  - `rendered_body` (text, not null)
  - `status` (string(32), not null, default `"pending"`)
  - `error_message` (text, null)
  - `sent_by_user_id` (UUID, null)
  - `sent_at` (timestamptz, null)
  - `created_at`, `updated_at` (timestamptz)
- Indexes (migration `b0c2d8e8f9a0...`):
  - `ix_outbound_messages_tenant_status` (`tenant_id`, `status`)
  - `ix_outbound_messages_tenant_customer` (`tenant_id`, `customer_id`)
  - `ix_outbound_messages_tenant_template` (`tenant_id`, `template_id`)
  - `ix_outbound_messages_tenant_created_at` (`tenant_id`, `created_at`)
- RLS:
  - Enabled (policy: `tenant_isolation_outbound_messages`)

---

### `audit_log`
Model: `modules/audit/models/audit_log_orm.py`

- Columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK → `tenants.id` ON DELETE CASCADE)
  - `user_id` (UUID, null)
  - `action` (string(32), not null)
  - `entity_type` (string(64), not null)
  - `entity_id` (UUID, not null)
  - `before` (JSON/JSONB, null)
  - `after` (JSON/JSONB, null)
  - `created_at` (timestamptz)
- Indexes:
  - `ix_audit_log_tenant_created_at` (`tenant_id`, `created_at`)
  - `ix_audit_log_tenant_entity` (`tenant_id`, `entity_type`, `entity_id`)
- RLS:
  - Enabled (policy: `tenant_isolation_audit_log`)

