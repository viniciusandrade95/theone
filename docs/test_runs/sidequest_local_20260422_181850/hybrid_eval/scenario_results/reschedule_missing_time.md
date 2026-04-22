# reschedule_missing_time

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"sidequest-20260422_181850-20260422T171856Z-ca59dad3-reschedule_missing_time-1"}
- step 1: assertion_failure: expected status collecting, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: reply missing expected text: horário
- step 1: assertion_failure: expected slot new_date to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
