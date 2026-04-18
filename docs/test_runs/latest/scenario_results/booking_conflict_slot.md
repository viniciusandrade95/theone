# booking_conflict_slot

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888
Turn 1 assistant: 
Turn 2 user: sim
Turn 2 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T143935Z-a6fbf12b-booking_conflict_slot-1"}
- step 1: expected route workflow, got None
- step 1: expected workflow book_appointment, got None
- step 1: expected slot service to be present
- step 1: expected slot date to be present
- step 1: expected slot time to be present
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T143935Z-a6fbf12b-booking_conflict_slot-2"}
- step 2: expected route workflow, got None
- step 2: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
