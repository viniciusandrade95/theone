# generated_i0001_01_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-3888768933a947e5
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: Tudo bem, vamos ajustar a data. Qual nova data funciona melhor para você?
Turn 2 user: meu corte
Turn 2 assistant: Perfeito, ajustei para Corte. Qual nova data funciona melhor para você?
Turn 3 user: 16h
Turn 3 assistant: Beleza, vamos ajustar a data. Qual nova data funciona melhor para você?
Turn 4 user: pode
Turn 4 assistant: 
```

## Failures

- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260419T152928Z-3288eeda-generated_i0001_01_seed_reschedule_ambiguous-4"}
- step 4: assertion_failure: expected workflow reschedule_appointment, got None
- step 3: heuristic_failure: Repeated date question

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
