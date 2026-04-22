# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: 
Turn 2 user: sim, pode confirmar
Turn 2 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T035107Z-4de57759-reschedule_happy_path-1"}
- step 1: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 1: assertion_failure: expected slot new_date to be present
- step 1: assertion_failure: expected slot new_time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260422T035107Z-4de57759-reschedule_happy_path-2"}
- step 2: assertion_failure: expected status completed, got response=None workflow=None
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
