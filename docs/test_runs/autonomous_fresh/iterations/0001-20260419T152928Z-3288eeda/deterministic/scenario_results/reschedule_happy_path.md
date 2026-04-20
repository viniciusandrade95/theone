# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-ea30c5390bf844b4
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: A integração está temporariamente indisponível. Vou encaminhá-lo(a) para atendimento humano.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: 
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 1: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260419T152928Z-3288eeda-reschedule_happy_path-2"}
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
