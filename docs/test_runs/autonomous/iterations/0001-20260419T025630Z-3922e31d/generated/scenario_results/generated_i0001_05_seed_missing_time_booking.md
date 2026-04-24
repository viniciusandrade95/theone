# generated_i0001_05_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-e3a0938a2b1c4294
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Qual serviço você procura? Posso ajudar com Corte.
Turn 2 user: corte amanhã
Turn 2 assistant: Tudo certo, alterei para Corte. Qual horário fica melhor pra você?
Turn 3 user: de tarde
Turn 3 assistant: 
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Perfeito, ajustei tudo aqui. Qual horário fica melhor pra você?
Turn 5 user: ok
Turn 5 assistant: Qual horário te funciona melhor?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260419T025630Z-3922e31d-generated_i0001_05_seed_missing_time_booking-3"}
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 5: heuristic_failure: Repeated time question
- heuristic_failure: Expected final status awaiting_confirmation, got collecting

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
