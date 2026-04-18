# booking_missing_phone

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-8236b18a261a4ead
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User
Turn 1 assistant: Perfeito, troquei para Corte: resumo do pré‑agendamento – Corte no dia 19 de abr às 15:00, tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: pode confirmar
Turn 2 assistant: Para confirmar, você poderia me informar o telefone do cliente?
Turn 3 user: 11999998888
Turn 3 assistant: 
```

## Failures

- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"audit-eval-20260418T152209Z-5b04bff0-booking_missing_phone-3"}
- step 3: assertion_failure: expected route workflow, got None
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: reply missing expected text: confirmar

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
