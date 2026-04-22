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

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_with_colloquial_ptbr-1"}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_with_colloquial_ptbr-2"}
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_with_colloquial_ptbr-3"}
- step 3: assertion_failure: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
