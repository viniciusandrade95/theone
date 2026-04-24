# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-0dd516df2fe149c0
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você deseja? Posso te ajudar com Corte.
Turn 2 user: Corte
Turn 2 assistant: Tudo certo, ajustei para Corte. Qual dia funciona melhor para você?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo! Qual horário funciona melhor pra você?
Turn 4 user: 16h17
Turn 4 assistant: Ótimo, já ajustei o horário: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo e posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo e posso encaminhar para confirmação humana?
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Ótimo! Pré-reserva criada com sucesso.
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
