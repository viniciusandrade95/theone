# generated_i0001_03_seed_booking_with_faq_interruption

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-212677bf5af447ba
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar corte amanhã
Turn 1 assistant: Tudo certo, mudei para Corte. Qual horário fica melhor pra você?
Turn 2 user: opa, quanto custa?
Turn 2 assistant: Claro, posso te informar: qual serviço quer saber o preço? Temos Corte; se quiser, retomamos o agendamento depois.
Turn 3 user: beleza, 16h17 então
Turn 3 assistant: Tudo certo! Ajustei o horário: pré‑agendamento de Corte no dia 20 de abr às 16:17. Posso enviar para a equipe confirmar?
Turn 4 user: Audit User, 11999998888
Turn 4 assistant: 
Turn 5 user: sim, pode confirmar
Turn 5 assistant: Tudo certo! A pré‑reserva foi criada com sucesso.
```

## Failures

- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260419T031011Z-e2c01790-generated_i0001_03_seed_booking_with_faq_interruption-4"}
- step 4: assertion_failure: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
