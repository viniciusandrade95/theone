# generated_i0002_04_seed_booking_with_faq_interruption

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar corte amanhã
Turn 1 assistant: 
Turn 2 user: opa, quanto custa?
Turn 2 assistant: 
Turn 3 user: beleza, 16h17 então
Turn 3 assistant: 
Turn 4 user: Audit User, 11999998888
Turn 4 assistant: 
Turn 5 user: sim, pode confirmar
Turn 5 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-generated-20260422T172005Z-aa5bee6d-generated_i0002_04_seed_booking_with_faq_interruption-1"}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-generated-20260422T172005Z-aa5bee6d-generated_i0002_04_seed_booking_with_faq_interruption-2"}
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-generated-20260422T172005Z-aa5bee6d-generated_i0002_04_seed_booking_with_faq_interruption-3"}
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-generated-20260422T172005Z-aa5bee6d-generated_i0002_04_seed_booking_with_faq_interruption-4"}
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 5: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-generated-20260422T172005Z-aa5bee6d-generated_i0002_04_seed_booking_with_faq_interruption-5"}
- step 5: assertion_failure: expected workflow book_appointment, got None
- heuristic_failure: Expected final status completed, got unknown

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
