# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-a4aaeb697eac445c
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você gostaria de agendar? Posso ajudar com um corte.
Turn 2 user: Corte
Turn 2 assistant: Perfeito, já alterei para Corte. Quando prefere marcar?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo! Qual horário funciona melhor pra você?
Turn 4 user: 16h17
Turn 4 assistant: Tudo bem, ajustei o horário. Preciso apenas confirmar o pré-agendamento de Corte no dia 19 de abr às 16:17; posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 19 de abr às 16:17. Tudo certo e posso encaminhar para confirmação humana?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 5: assertion_failure: reply missing expected text: confirmar

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
