# booking_with_short_affirmations

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-8236b18a261a4ead
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Corte amanhã 16h17 Audit User 11999998888
Turn 1 assistant: 
Turn 2 user: ok
Turn 2 assistant: Antes de confirmar, pode me informar o nome do cliente para este agendamento?
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"audit-eval-20260418T155718Z-d11131a8-booking_with_short_affirmations-1"}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
