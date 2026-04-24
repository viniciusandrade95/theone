# Assistant Conversation Analytics - Execution Log

## Goal

Implement a minimal, production-usable conversation analytics layer for CRM assistant and WhatsApp flows so operators can reconstruct conversations, measure outcomes, and identify where assistant flows break.

## Problem statement

The system already persisted parts of assistant/WhatsApp activity, but analytics were fragmented:

- Dashboard assistant sessions and messages existed in chatbot-specific tables.
- WhatsApp inbound/outbound messages existed in messaging tables.
- Assistant funnel events existed, but did not consistently represent conversation starts, resets, prebook failures, or missing-data blockers.
- Existing analytics endpoints reported aggregate funnel counts, but did not let an engineer list conversations with outcomes or open a conversation with turns and events.

This made it hard to answer operational/product questions such as:

- How many conversations started?
- Which conversations reached prebook?
- Which failed because required customer identity was missing?
- Which requested handoff?
- Which messages/turns led to fallback or operational failure?

## Root cause

The underlying data existed in multiple places, but there was no single read path or normalized event taxonomy connecting:

- dashboard assistant turns
- WhatsApp inbound/outbound turns
- assistant prebook lifecycle
- handoff lifecycle
- conversion confirmation

The missing piece was not a new large architecture. It was a consistent event rollup and tenant-scoped read endpoints that reuse existing persistence.

## Scope

In scope:

- Reuse existing conversation/session/message/event tables.
- Add missing assistant funnel event names for conversation analytics.
- Emit conversation start/reset events for dashboard assistant.
- Emit assistant message received/replied events for WhatsApp bot flow.
- Emit prebook failure and missing-data events from `/crm/assistant/prebook`.
- Derive conversation outcomes from actual persisted events.
- Add tenant-scoped listing/detail/outcome endpoints.
- Add automated tests for dashboard, WhatsApp, and blocked prebook analytics.
- Document the model and limitations.

Out of scope:

- Full anonymization/redaction layer.
- Background job that marks conversations abandoned.
- Frontend analytics UI.
- Rewriting existing message/session models.

## Files changed

- `app/http/main.py`
- `app/http/routes/assistant_analytics.py`
- `app/http/routes/assistant_prebook.py`
- `app/http/routes/assistant_prebook_schemas.py`
- `app/http/routes/chatbot.py`
- `app/http/routes/crm.py`
- `modules/assistant/service/funnel_events.py`
- `modules/assistant/service/conversation_analytics.py`
- `modules/messaging/service/inbound_webhook_service.py`
- `tests/api/test_assistant_conversation_analytics_api.py`
- `docs/assistant-conversation-analytics.md`
- `docs/execution/assistant_conversation_analytics_execution_log.md`
- `docs/execution/assistant_conversation_analytics_test_report.md`
- `docs/execution/assistant_conversation_analytics_examples.md`

## Design decisions

- Use `assistant_funnel_events` as the event log/join point instead of creating a parallel analytics event table.
- Keep the outcome taxonomy derived from evidence, not manually stored as a mutable status.
- Keep message text in existing message tables and only expose it from the conversation detail endpoint.
- Treat detail endpoint output as sensitive internal data because it includes conversation text and possible PII.
- Add `conversation_id` as optional to the assistant prebook payload so future chatbot callbacks can be correlated precisely without breaking existing callers.
- Keep WhatsApp analytics emission best-effort so inbound message processing is not blocked by analytics write failures.

## Behavior before

- `/analytics/assistant/overview`, `/funnel`, `/channels`, `/templates`, and `/conversions` provided aggregate counts.
- Dashboard assistant messages were persisted, but there was no analytics endpoint to reconstruct a conversation from turns and events.
- WhatsApp inbound/outbound turns were persisted separately from assistant analytics.
- Prebook missing-data failures did not produce specific analytics events.
- Operator-confirmed conversion events did not try to link back to the originating assistant conversation/session.

## Behavior after

- `GET /analytics/assistant/conversations` lists tenant-scoped assistant conversations with:
  - `conversation_id`
  - `assistant_session_id`
  - `surface`
  - started/last activity timestamps
  - derived outcome
  - signal counts
  - abandoned candidate flag
- `GET /analytics/assistant/conversations/{conversation_id}` returns:
  - metadata
  - derived outcome
  - turns
  - analytics events
  - signals for fallback/prebook/handoff/missing data/failure
- `GET /analytics/assistant/outcomes` returns outcome counts by period.
- Dashboard assistant flow emits conversation start/reset events.
- WhatsApp assistant flow emits conversation start, message received, and message replied events.
- Prebook failures and missing customer identity/phone blockers are represented as analytics events.

## Risks / follow-ups

- Conversation detail includes message text and should remain an internal/admin surface. A redaction/PII masking policy should be added before broader exposure.
- Abandonment is currently `abandoned_candidate`, derived from last activity age. A scheduled job should persist explicit `abandoned` events if this becomes operationally important.
- `conversation_id` correlation for prebook depends on the upstream assistant sending it. Existing callers without it still work, but correlation may rely on `session_id`.
- The current endpoints are backend-only. A dedicated frontend/admin UI remains a separate task.

