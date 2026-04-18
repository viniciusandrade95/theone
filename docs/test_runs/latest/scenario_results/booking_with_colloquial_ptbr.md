# booking_with_colloquial_ptbr

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: opa, queria corta o cabelo amanha la pras 4 e 17 da tarde
Turn 1 assistant: 
Turn 2 user: meu nome é Audit User e o zap é 11999998888
Turn 2 assistant: 
Turn 3 user: isso, manda bala
Turn 3 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_colloquial_ptbr-1"}
- step 1: expected workflow book_appointment, got None
- step 1: expected slot service to be present
- step 1: expected slot date to be present
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_colloquial_ptbr-2"}
- step 2: expected workflow book_appointment, got None
- step 2: reply missing expected text: confirmar
- step 3: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-booking_with_colloquial_ptbr-3"}
- step 3: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
