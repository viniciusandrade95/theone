# booking_with_short_affirmations

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Corte amanhã 16h17 Audit User 11999998888
Turn 1 assistant: 
Turn 2 user: ok
Turn 2 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172048Z-9a943207-booking_with_short_affirmations-1"}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172048Z-9a943207-booking_with_short_affirmations-2"}
- step 2: assertion_failure: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
