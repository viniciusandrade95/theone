# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-41e76d6c17a44f15
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você quer fazer por aqui? Posso te ajudar com Corte, Barba ou Sobrancelha.
Turn 2 user: Corte
Turn 2 assistant: Perfeito, ajustei para Corte. Qual dia fica melhor para você passar por aqui?
Turn 3 user: amanhã
Turn 3 assistant: Perfeito, ajustei isso por aqui. Que horário te atende melhor por aqui?
Turn 4 user: 16h17
Turn 4 assistant: Perfeito, ajustei o horário. Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Perfeito. Integração temporariamente indisponível. Vou encaminhar para atendimento humano.
```

## Failures

- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 6: assertion_failure: expected action_result.ok=True, got False

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
