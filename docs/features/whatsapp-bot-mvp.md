# WhatsApp ↔ assistant (MVP)

## Goal
Allow a real WhatsApp customer message to:

1. be ingested via a Meta WhatsApp Cloud webhook
2. be routed to the correct tenant (via `whatsapp_accounts.phone_number_id`)
3. be forwarded to `chatbot1`
4. be replied to via WhatsApp Cloud API
5. persist basic continuity (`assistant_session_id`) so the next message continues the same bot session

This is intentionally a thin slice (no full queue/SLA system, no complex NLP).

## Required configuration

WhatsApp webhook security:
- `WHATSAPP_WEBHOOK_SECRET` (used to validate `X-Hub-Signature-256`)
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (used for GET verification handshake)

WhatsApp Cloud sending:
- `WHATSAPP_CLOUD_ACCESS_TOKEN`
- (tenant data) create an active WhatsApp account: `POST /messaging/whatsapp-accounts` with `phone_number_id`

Chatbot orchestration:
- `CHATBOT_SERVICE_BASE_URL`

## Public webhook endpoint (Meta Webhooks)

Configure Meta to call:
- `GET /messaging/webhook` (verification)
- `POST /messaging/webhook` (events)

`POST /messaging/webhook` supports:
- inbound text messages → enqueued to worker (`/messaging/inbound` path internally)
- delivery status callbacks → processed inline (updates `outbound_messages.delivery_status`)

## Bot reply behavior

When an inbound message is processed, the system will:

1. resolve tenant via `whatsapp_accounts` routing
2. ensure a tenant-scoped `Customer` exists for the phone (auto-creates if missing)
3. get or create a `Conversation` for `(tenant_id, customer_id, channel="whatsapp")`
4. call `chatbot1 /message` with:
   - `surface="whatsapp"`
   - `conversation_id=<conversation.id>`
   - `session_id=<conversation.assistant_session_id>`
   - `user_id=<customer_id>` (stable UUID-like scoping)
5. persist returned `session_id` back to the conversation (`assistant_session_id`)
6. send reply text via WhatsApp Cloud API
7. persist the outbound reply to `outbound_messages` (`type="assistant_whatsapp_reply"`)

Duplicate inbound events are deduped via `webhook_events` and will not trigger double replies.

## Operational visibility

- inbound customer text is recorded as a CRM interaction of type `whatsapp`
- bot reply is recorded as a CRM interaction of type `assistant_whatsapp_reply`
- outbound lifecycle is visible via `/crm/outbound/messages` (per tenant)

## Notes / deferrals

- Only text messages are supported in this MVP.
- If `CHATBOT_SERVICE_BASE_URL` or `WHATSAPP_CLOUD_ACCESS_TOKEN` is missing, inbound is still recorded but no bot reply is sent.
- Error handling is best-effort: inbound processing should not dead-letter solely due to chatbot/provider unavailability.

