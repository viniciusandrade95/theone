# reschedule_conflict

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 15h
Turn 1 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172005Z-aa5bee6d-reschedule_conflict-1"}
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: reply missing any expected text: indisponível, disponibilidade, sugerir, remarcação, confirmar

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
