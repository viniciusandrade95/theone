# faq_then_booking

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Tem vaga amanhã?
Turn 1 assistant: 
Turn 2 user: Quero corte às 16h17 para Audit User, telefone 11999998888
Turn 2 assistant: 
Turn 3 user: sim pode confirmar
Turn 3 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-faq_then_booking-1"}
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-faq_then_booking-2"}
- step 2: expected workflow book_appointment, got None
- step 2: expected slot service to be present
- step 2: expected slot time to be present
- step 3: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T141140Z-0799804c-faq_then_booking-3"}
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
