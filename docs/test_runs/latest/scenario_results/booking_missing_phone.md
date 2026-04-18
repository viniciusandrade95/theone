# booking_missing_phone

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User
Turn 1 assistant: 
Turn 2 user: pode confirmar
Turn 2 assistant: 
Turn 3 user: 11999998888
Turn 3 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_missing_phone-1"}
- step 1: expected status awaiting_confirmation, got response=None workflow=None
- step 1: expected route workflow, got None
- step 1: expected workflow book_appointment, got None
- step 1: expected slot service to be present
- step 1: expected slot date to be present
- step 1: expected slot time to be present
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_missing_phone-2"}
- step 2: expected route workflow, got None
- step 2: expected workflow book_appointment, got None
- step 2: reply missing expected text: telefone
- step 3: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_missing_phone-3"}
- step 3: expected route workflow, got None
- step 3: expected workflow book_appointment, got None
- step 3: reply missing expected text: confirmar

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
