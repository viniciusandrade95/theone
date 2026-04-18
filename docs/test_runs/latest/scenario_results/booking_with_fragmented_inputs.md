# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: 
Turn 2 user: Corte
Turn 2 assistant: 
Turn 3 user: amanhã
Turn 3 assistant: 
Turn 4 user: 16h17
Turn 4 assistant: 
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_fragmented_inputs-1"}
- step 1: expected workflow book_appointment, got None
- step 1: reply missing expected text: serviço
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_fragmented_inputs-2"}
- step 2: expected workflow book_appointment, got None
- step 2: expected slot service to be present
- step 3: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_fragmented_inputs-3"}
- step 3: expected workflow book_appointment, got None
- step 3: expected slot service to be present
- step 3: expected slot date to be present
- step 4: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_fragmented_inputs-4"}
- step 4: expected workflow book_appointment, got None
- step 4: expected slot service to be present
- step 4: expected slot date to be present
- step 4: expected slot time to be present
- step 5: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_fragmented_inputs-5"}
- step 5: expected workflow book_appointment, got None
- step 5: reply missing expected text: confirmar

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
