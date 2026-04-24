# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-2062f17835044b1b
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: Corte
Turn 2 assistant: Perfeito, ajustei para Corte. Qual dia fica melhor para você?
Turn 3 user: amanhã
Turn 3 assistant: Perfeito, ajustei isso por aqui. Que horário te atende melhor?
Turn 4 user: 16h17
Turn 4 assistant: Perfeito, ajustei o horário. Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: 
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Perfeito. Pré-reserva criada com sucesso.
```

## Failures

- step 5: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-deterministic-20260419T152928Z-3288eeda-booking_with_fragmented_inputs-5"}
- step 5: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 5: assertion_failure: expected route workflow, got None
- step 5: assertion_failure: expected workflow book_appointment, got None
- step 5: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 5: assertion_failure: expected slot service to be present
- step 5: assertion_failure: expected slot date to be present
- step 5: assertion_failure: expected slot time to be present
- step 5: assertion_failure: expected slot customer_name to be present
- step 5: assertion_failure: expected slot phone to be present
- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
