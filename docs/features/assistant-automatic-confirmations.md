# Assistant automatic confirmations (MVP)

## Goal
Send **automatic, provider-backed confirmations** for a small set of assistant/business outcomes, using the existing outbound module as the system of record.

This is intentionally not a “journey/campaign” system.

## Supported triggers (this PR)

1. **Prebook created** (`POST /crm/assistant/prebook` → `status="created"`)
   - Creates an `outbound_messages` row with `trigger_type="assistant_prebook_created"`.
2. **Handoff created** (assistant quick wins orchestration)
   - Creates an `outbound_messages` row with `trigger_type="assistant_handoff_created"`.

Future triggers (not implemented here): quote created, consult created.

## Templates (source of truth for content)

Templates are tenant-scoped (`/crm/outbound/templates`) and must be created as **active** for the automation to send.

Supported template types (new):
- `assistant_prebook_confirmation`
- `assistant_handoff_confirmation`

Supported channels:
- `whatsapp`
- `email`

Supported template variables (unchanged):
- `{{customer_name}}`
- `{{appointment_date}}`, `{{appointment_time}}` (when an appointment exists)
- `{{service_name}}`, `{{location_name}}` (when an appointment exists)
- `{{business_name}}` (tenant settings)

## Channel selection and fallback (deterministic)

For each trigger, the system tries channels in this order:

1. `whatsapp`
2. `email`

Rules:
- A channel is considered only if an active template exists for `(type, channel)`.
- WhatsApp requires a valid customer phone and an active WhatsApp account + Cloud token.
- Email requires a valid customer email and SMTP configuration.
- If a channel attempt fails (missing recipient, provider not configured, provider send failure), the system falls back to the next channel.

## Idempotency and duplicate prevention

Automatic confirmations use `outbound_messages.idempotency_key` with the shape:

`auto:<scope>:<channel>`

This prevents repeated sends for the same trigger+entity+channel in retries.

Hardening note:
- if a prior attempt exists with `status=failed`, the system may retry and/or fall back to the next channel using the same idempotency key, without creating a new row.

## Provider configuration

WhatsApp (Cloud API):
- `WHATSAPP_CLOUD_ACCESS_TOKEN`
- Active row in `whatsapp_accounts` for the tenant (`provider="meta"`, `status="active"`)

Email (SMTP):
- `SMTP_HOST`, `SMTP_FROM`
- Optional: `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_TIMEOUT_SECONDS`, `SMTP_USE_STARTTLS`

## Failure semantics

Confirmations are **best-effort**:
- business actions (prebook/handoff) never fail because messaging failed
- failures are recorded in `outbound_messages` (`status="failed"`, `error_code`, `error_message`)
