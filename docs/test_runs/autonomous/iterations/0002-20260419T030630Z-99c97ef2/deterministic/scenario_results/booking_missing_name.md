# booking_missing_name

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-d7093d4f59ba4478
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h
Turn 1 assistant: Perfeito, alterei para Corte. Resumo para confirmação: pré‑agendamento de Corte no dia 20 de abr às 15:00, tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: sim
Turn 2 assistant: 
Turn 3 user: Audit User
Turn 3 assistant: 
Turn 4 user: pode confirmar
Turn 4 assistant: Oi! Antes de confirmar, qual o nome do cliente para este agendamento?
```

## Failures

- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"autonomous-eval-deterministic-20260419T030630Z-99c97ef2-booking_missing_name-2"}
- step 2: upstream_runtime_failure: expected route workflow, got None
- step 2: upstream_runtime_failure: expected workflow book_appointment, got None
- step 2: upstream_runtime_failure: reply missing expected text: nome
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"autonomous-eval-deterministic-20260419T030630Z-99c97ef2-booking_missing_name-3"}
- step 3: upstream_runtime_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 3: upstream_runtime_failure: expected route workflow, got None
- step 3: upstream_runtime_failure: expected workflow book_appointment, got None
- step 3: upstream_runtime_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 3: upstream_runtime_failure: expected slot service to be present
- step 3: upstream_runtime_failure: expected slot date to be present
- step 3: upstream_runtime_failure: expected slot time to be present
- step 3: upstream_runtime_failure: expected slot customer_name to be present
- step 4: assertion_failure: reply missing expected text: telefone
- step 4: assertion_failure: expected action_result.missing_customer_phone=True, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
