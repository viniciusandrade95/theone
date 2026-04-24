# Assistant Conversation Analytics - Test Report

## Test strategy

The tests cover the analytics layer at API level because the epic changes cross-route behavior:

- dashboard assistant message persistence and analytics rollup
- WhatsApp inbound/outbound bot reply persistence and analytics rollup
- prebook missing-data blocker event emission
- tenant-scoped conversation listing/detail endpoints
- existing assistant aggregate analytics regressions
- existing WhatsApp bot reply regressions

## Unit tests added

No standalone unit tests were added. The outcome derivation logic is exercised through integration-style API tests because the key risk is cross-model persistence and query behavior.

## Integration tests added

Added `tests/api/test_assistant_conversation_analytics_api.py`.

Coverage:

- Dashboard conversation can be listed through `/analytics/assistant/conversations`.
- Dashboard conversation detail includes persisted user/assistant turns.
- WhatsApp inbound conversation can be listed through `/analytics/assistant/conversations`.
- WhatsApp conversation detail includes inbound user turn and assistant outbound turn.
- Prebook missing phone returns a blocked request and records analytics outcome `blocked_missing_data`.
- Conversation detail exposes `missing_customer_phone` signal.

## Manual test scenarios

Recommended manual scenarios for deployed validation:

- Dashboard user sends one assistant message; verify conversation appears in `/analytics/assistant/conversations`.
- Open the conversation detail; verify the turn sequence is reconstructable.
- WhatsApp inbound user sends a message; verify inbound and bot reply appear in detail.
- Trigger booking confirmation without customer phone; verify no prebook success is recorded and outcome is `blocked_missing_data`.
- Trigger a successful prebook; verify outcome becomes `completed_prebook`.
- Operator confirms a pending assistant prebook to booked; verify conversion outcome can become `completed_booking` when correlation data exists.

## Results

Commands run:

```bash
cd /home/vinicius/system-audit/workspace/theone
./venv/bin/pytest -q tests/api/test_assistant_conversation_analytics_api.py
./venv/bin/pytest -q tests/api/test_assistant_analytics_api.py tests/api/test_whatsapp_bot_reply_api.py
```

Results:

- `tests/api/test_assistant_conversation_analytics_api.py`: 2 passed
- `tests/api/test_assistant_analytics_api.py tests/api/test_whatsapp_bot_reply_api.py`: 5 passed

Note: running `pytest` with the system Python failed because the system environment was missing packages such as `httpx` and `sqlalchemy`. The repo virtualenv at `./venv/bin/pytest` was used for verification.

## Regressions checked

- Existing assistant analytics overview/funnel/conversion tests still pass.
- Existing WhatsApp bot reply tests still pass.
- Dashboard chatbot proxy remains compatible with existing upstream response shape.
- WhatsApp inbound processing remains best-effort for analytics writes.

## Remaining gaps

- No test yet for explicit `abandoned_candidate` age threshold.
- No test yet for operator confirmation producing `completed_booking` with `conversation_id` correlation.
- No test yet for filtering conversations by `outcome` and `surface`.
- No test yet for PII redaction because this epic does not implement redaction.

