# booking_user_changes_time_mid_flow

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888
Turn 1 assistant: 
Turn 2 user: Na verdade muda para 16h17
Turn 2 assistant: 
Turn 3 user: sim
Turn 3 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_user_changes_time_mid_flow-1"}
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_user_changes_time_mid_flow-2"}
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: 16
- step 2: assertion_failure: expected slot service to be present
- step 2: assertion_failure: expected slot date to be present
- step 2: assertion_failure: expected slot time to be present
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T034942Z-aef20d8a-booking_user_changes_time_mid_flow-3"}
- step 3: assertion_failure: expected route workflow, got None
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
