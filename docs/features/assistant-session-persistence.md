# Assistant session persistence (MVP)

This document describes the lightweight persistence used to keep assistant interactions coherent across turns without building a full chat platform.

## Goals

- Continue assistant flows (booking / handoff) without repeating the same questions unnecessarily.
- Persist a compact operational state for the active conversation scope.
- Persist a small turn history for support/debugging.
- Preserve strict multitenancy and existing `chatbot_conversation_sessions` behavior.

## Data model

### `chatbot_conversation_sessions` (extended)

Existing session row is still the canonical scope: **(tenant_id, user_id, surface)**.

Added continuity fields:

- `last_intent` (string, nullable): last normalized intent returned by upstream chatbot.
- `last_intent_confidence` (float, nullable): optional confidence if upstream provides it.
- `state_payload` (json/jsonb, nullable): compact assistant state (e.g. `handoff` marker, booking context).
- `context_payload` (json/jsonb, nullable): compact extracted context (e.g. `slots`, `context`).
- `conversation_epoch` (int, default 0): incremented on reset to prevent stale state bleed.

Notes:
- Keep `state_payload`/`context_payload` low-risk and avoid PII when possible.
- Storage is best-effort; large blobs are truncated/dropped.

### `chatbot_conversation_messages` (new)

Stores a compact history of recent turns.

Key fields:
- `conversation_id`, `tenant_id`, `user_id`, `surface`
- `role`: `user` / `assistant` / `system`
- `content`: text (user message or assistant reply)
- `intent`: assistant intent when applicable
- `epoch`: copied from session `conversation_epoch`
- `meta`: small JSON metadata (no raw upstream dumps)

Retention:
- Best-effort retention of the **last 50 messages per (conversation_id, epoch)**.

## Runtime behavior

### `/api/chatbot/message`

On each request:
- Appends a `user` message row.
- Calls upstream chatbot as before (no contract changes required).
- Appends an `assistant` message row with normalized fields.
- Updates `last_intent`, `state_payload`, and `context_payload` best-effort.

Continuity:
- If `customer_id` is omitted on a later turn, the persisted session `customer_id` is reused for upstream payload.

### `/api/chatbot/reset`

On reset:
- Clears continuity fields (`last_intent`, `state_payload`, `context_payload`).
- Increments `conversation_epoch`.
- Appends a `system` reset marker message.

History is not deleted; it is segmented by `epoch` to keep the active flow isolated.

## Deferred / intentionally not implemented

- Full intent engine owned by `theone`.
- A complete assistant orchestration state machine.
- A staff UI for viewing assistant history (API/DB visibility is sufficient for MVP).
- PII redaction beyond existing guardrails (should be revisited before production logging/export).

