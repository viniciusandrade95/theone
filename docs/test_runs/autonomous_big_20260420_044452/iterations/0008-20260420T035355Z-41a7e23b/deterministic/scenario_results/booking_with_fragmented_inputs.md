# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-c5238405352048da
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
Turn 4 assistant: Perfeito, ajustei o horário. Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Perfeito. Pré-reserva criada com sucesso.
```

## Failures

- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 5: heuristic_failure: Repeated date question

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
