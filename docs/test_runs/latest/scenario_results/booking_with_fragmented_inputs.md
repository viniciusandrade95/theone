# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-64cb6a3d6a424556
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você prefere? Posso te ajudar com o corte.
Turn 2 user: Corte
Turn 2 assistant: Perfeito, ajustei para Corte! Em qual dia você prefere marcar?
Turn 3 user: amanhã
Turn 3 assistant: Perfeito, já ajustei aqui. Qual horário funciona melhor para você?
Turn 4 user: 16h17
Turn 4 assistant: Horário ajustado! Pré-agendamento de Corte: 19 de abr às 16:17. Tudo certo? Posso enviar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte em 19 de abr às 16:17. Tudo certo, posso encaminhar para confirmação humana?
```

## Failures

- step 5: assertion_failure: expected slot customer_name to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
