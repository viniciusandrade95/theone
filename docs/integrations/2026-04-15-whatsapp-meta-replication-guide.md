# WhatsApp (Meta Cloud) – Replication / Validation Guide (2026-04-15)

This repo already supports an end-to-end WhatsApp Cloud (Meta) integration:
- inbound webhook entrypoint + HMAC verification
- tenant routing via `whatsapp_accounts` (`provider + phone_number_id`)
- provider-backed outbound (Graph API)
- `wa.me` deeplink fallback (manual assisted send)
- outbound history + delivery lifecycle (callbacks)

This guide consolidates the existing behavior and how to configure + validate it without introducing new architecture.

## 0) Product framing (what “connect” means)

In TheOne, “Connect WhatsApp number” means creating a mapping between:
- `provider` (currently: `meta`)
- Meta `phone_number_id` (an internal ID that identifies your WhatsApp Business number in Meta)

This mapping is the routing key TheOne uses to safely resolve which tenant should receive:
- inbound WhatsApp webhooks (messages)
- delivery callbacks (statuses)

## 1) Environment variables (normalized)

WhatsApp / Meta variables (see `.env.example`):

- `WHATSAPP_WEBHOOK_SECRET`
  - Meta **App Secret**.
  - Used to validate `X-Hub-Signature-256` on inbound + delivery callbacks.
  - Required for: `POST /messaging/webhook`, `POST /messaging/inbound`, `POST /messaging/delivery`.
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
  - Any string you choose.
  - Used for `GET /messaging/webhook` verification handshake (`hub.verify_token`).
- `WHATSAPP_CLOUD_ACCESS_TOKEN`
  - Token used for Graph API calls (provider-backed outbound).
- `WHATSAPP_CLOUD_API_VERSION`
  - Example: `v19.0` (defaults to `v19.0`).
- `WHATSAPP_CLOUD_TIMEOUT_SECONDS`
  - HTTP timeout for Graph API calls (integer seconds).

## 2) Endpoints in TheOne (what to configure in Meta)

### 2.1 GET webhook verification flow

Endpoint: `GET /messaging/webhook`

Meta sends a request with query params:
- `hub.mode=subscribe`
- `hub.verify_token=<your token>`
- `hub.challenge=<random string>`

TheOne behavior:
- If `WHATSAPP_WEBHOOK_VERIFY_TOKEN` is missing → `503 whatsapp_verify_token_not_configured`
- If token/mode mismatch → `403 whatsapp_verify_token_invalid`
- If valid → responds `200` with the plain-text `hub.challenge`

### 2.2 POST inbound webhook flow (Meta format)

Endpoint: `POST /messaging/webhook`

What this endpoint does:
- Validates `X-Hub-Signature-256` using `WHATSAPP_WEBHOOK_SECRET` (Meta App Secret).
- Extracts inbound text messages from the Meta payload (`entry[].changes[].value.messages[]`).
- Enqueues each extracted inbound event for async processing (and optional bot reply).
- Extracts delivery status events (`entry[].changes[].value.statuses[]`) and processes them inline (delivery lifecycle).

Tenant routing:
- Tenant is resolved via `whatsapp_accounts` using `provider=meta` + `metadata.phone_number_id`.
- Inbound messages are routed in async processing (tenant resolution happens downstream).
- Delivery callbacks are routed inline before updating outbound history/lifecycle.

### 2.3 POST inbound webhook flow (normalized/internal payload)

Endpoint: `POST /messaging/inbound`

This is a normalized ingress (useful for testing / relays) that accepts:
- `provider` (default: `meta`)
- `external_event_id`, `phone_number_id`, `message_id`, `from_phone`, `text`, optional `to_phone`

It still requires the same signature header (`X-Hub-Signature-256`) and uses the same tenant routing mechanism downstream.

### 2.4 Provider-backed outbound flow

Primary endpoint: `POST /crm/outbound/send`

Behavior (high level):
- If a WhatsApp account mapping exists for the tenant (`/messaging/whatsapp-accounts`) **and**
  `WHATSAPP_CLOUD_ACCESS_TOKEN` is configured, TheOne sends via WhatsApp Cloud API (Graph).
- On success:
  - `outbound_messages.provider_message_id` is stored.
  - `delivery_status` starts as `accepted`.
  - No `wa.me` URL is returned.

See `docs/features/outbound-basic-mvp.md` for the product-level MVP behavior and status fields.

### 2.5 Fallback `wa.me` flow (manual assisted send)

If provider-backed send is not configured or fails, TheOne returns a `whatsapp_url` (`wa.me` deeplink).

Important:
- This is “assistive/manual send”, so delivery cannot be confirmed by the provider.
- `delivery_status` is treated as unconfirmed in this path (by design).

### 2.6 Delivery callback flow

Two supported ingestion paths:

1) Meta format (recommended): `POST /messaging/webhook`
   - Meta sends status updates under `entry[].changes[].value.statuses[]`.

2) Normalized/internal (tests/relay): `POST /messaging/delivery`
   - Accepts a simplified payload `{ provider, external_event_id, phone_number_id, provider_message_id, status, ... }`.

Both:
- Require `X-Hub-Signature-256` using `WHATSAPP_WEBHOOK_SECRET`
- Route tenant by `provider + phone_number_id`
- Dedupe by `(tenant_id, provider, external_event_id)`
- Update outbound history (`outbound_messages.delivery_status` + timestamps)

## 3) Minimum viable end-to-end validation (operator/developer)

### Prereqs
- Meta App + WhatsApp product configured.
- You know your `phone_number_id` and webhook subscription is active.
- TheOne is reachable publicly (or tunneled) for Meta to call it.

### Step A — Configure env
1) Set:
   - `WHATSAPP_WEBHOOK_SECRET` (Meta App Secret)
   - `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (any string)
2) For provider-backed outbound also set:
   - `WHATSAPP_CLOUD_ACCESS_TOKEN`
   - `WHATSAPP_CLOUD_API_VERSION`
   - `WHATSAPP_CLOUD_TIMEOUT_SECONDS`

### Step B — Configure Meta Webhooks
1) Callback URL: `https://<your-host>/messaging/webhook`
2) Verify token: same value as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
3) Subscribe to WhatsApp fields that include inbound messages and message status updates.

### Step C — Create WhatsApp account mapping (tenant routing)
Create a mapping so TheOne can route events by `provider + phone_number_id`:

Option A (recommended): Admin UI
- Go to `Admin → Connect WhatsApp number`
- Provider: `Meta (WhatsApp Cloud)`
- Paste the Meta `phone_number_id`
- Set status to `Active`

Option B: API
- `POST /messaging/whatsapp-accounts` with `{ "provider": "meta", "phone_number_id": "<phone_number_id>", "status": "active" }`

What is `phone_number_id`?
- It’s Meta’s internal identifier for your WhatsApp Business phone number (not the phone number like `+351...`).
- You can copy it from Meta / WhatsApp Manager (phone number details).

### Step D — Validate GET verification handshake
From Meta “Verify and save”, confirm:
- TheOne returns `200` with the `hub.challenge`.

### Step E — Validate inbound message handling
Send a real WhatsApp message to the configured number and confirm:
- TheOne accepts the webhook (`POST /messaging/webhook` returns `{"status":"accepted", ...}`).
- The inbound event is recorded/deduplicated and processed asynchronously.

### Step F — Validate outbound provider-backed send
Use the CRM outbound endpoint to send:
- If configured, you should see `provider_message_id` + `delivery_status=accepted`.
- If not configured (or provider fails), you should get a `whatsapp_url` deeplink fallback.

### Step G — Validate delivery lifecycle update
Confirm status callbacks reach TheOne:
- Via Meta: `POST /messaging/webhook` with `statuses[]`.
- The message should transition from `accepted` to `delivered/read` (when callbacks arrive).

## 4) Operational checklist (manual)

- Webhook verification:
  - `WHATSAPP_WEBHOOK_VERIFY_TOKEN` set
  - Meta verification handshake succeeds (`GET /messaging/webhook`)
- Webhook security:
  - `WHATSAPP_WEBHOOK_SECRET` set (Meta App Secret)
  - Requests without valid `X-Hub-Signature-256` are rejected
- Tenant routing:
  - `whatsapp_accounts` exists for each `phone_number_id` in use
  - Delivery callbacks update only the tenant that owns that `phone_number_id`
- Outbound sending:
  - `WHATSAPP_CLOUD_ACCESS_TOKEN` present for provider-backed sends
  - `WHATSAPP_CLOUD_API_VERSION` matches the Graph API version in your Meta app setup
  - `WHATSAPP_CLOUD_TIMEOUT_SECONDS` sane for your environment
- Delivery lifecycle:
  - Status callbacks are arriving (webhook subscribed to status fields)
  - Dedupe is working (replayed callbacks do not duplicate events)
