# Assistant Conversation Analytics - Examples

## Representative user messages

Dashboard:

```text
Ola dashboard
```

WhatsApp:

```text
Ola
```

Booking/prebook missing data:

```text
Quero marcar um corte amanha as 15:00
```

## Expected assistant responses

Dashboard generic assistant response:

```text
ok
```

WhatsApp bot reply:

```text
Ola! Como posso ajudar?
```

Missing phone before prebook:

```text
customer.phone is required when customer_id is not provided
```

Note: user-facing missing-phone prompting is handled in the upstream assistant flow. This CRM endpoint records the operational blocker when the callback reaches `/crm/assistant/prebook` without the required phone.

## Expected CRM side effects

Dashboard message:

- `chatbot_conversation_sessions` has/updates one session.
- `chatbot_conversation_messages` stores the user and assistant turns.
- `assistant_funnel_events` stores:
  - `assistant_conversation_started`
  - `assistant_message_received`
  - `assistant_message_replied`

WhatsApp inbound:

- `conversations` stores/updates the WhatsApp conversation.
- `messages` stores inbound user message.
- `outbound_messages` stores assistant reply.
- `assistant_funnel_events` stores:
  - `assistant_conversation_started`
  - `assistant_message_received`
  - `assistant_message_replied`

Prebook missing phone:

- No appointment should be created.
- `assistant_funnel_events` stores:
  - `assistant_prebook_requested`
  - `assistant_customer_phone_missing`
  - `assistant_prebook_failed`
- Conversation outcome should derive as `blocked_missing_data`.

Successful prebook:

- `appointments` gets a pending appointment with `needs_confirmation=true`.
- `assistant_prebook_requests` stores idempotency and appointment linkage.
- `assistant_funnel_events` stores `assistant_prebook_created`.
- Conversation outcome should derive as `completed_prebook`.

Operator confirms pending prebook:

- Appointment moves from `pending` to `booked`.
- `assistant_funnel_events` stores `assistant_conversion_confirmed`.
- Conversation outcome should derive as `completed_booking` when the prebook request has conversation/session correlation.

## Failure examples

Missing customer name and no `customer_id`:

```json
{
  "customer": {},
  "booking": {
    "service_id": "<service_uuid>",
    "requested_date": "2026-04-21",
    "requested_time": "12:00",
    "timezone": "Europe/Lisbon"
  }
}
```

Expected analytics:

- `assistant_customer_identity_missing`
- `assistant_prebook_failed`
- outcome `blocked_missing_data`

Missing customer phone and no `customer_id`:

```json
{
  "customer": {
    "name": "Alice"
  },
  "booking": {
    "service_id": "<service_uuid>",
    "requested_date": "2026-04-21",
    "requested_time": "12:00",
    "timezone": "Europe/Lisbon"
  }
}
```

Expected analytics:

- `assistant_customer_phone_missing`
- `assistant_prebook_failed`
- outcome `blocked_missing_data`

## Edge-case examples

Repeated prebook callback with same idempotency key:

- Existing idempotency behavior should prevent duplicate appointment creation.
- Analytics should not double-count `assistant_prebook_created` when the created appointment event is deduped.

Conversation reset:

```text
User resets dashboard assistant conversation
```

Expected analytics:

- `assistant_conversation_reset`
- new activity remains attached to same conversation id with incremented epoch where the existing session model applies it.

Conversation with fallback only:

- If a flow records `assistant_fallback` without prebook, conversion, handoff, or operational failure, outcome derives as `fallback_only`.

