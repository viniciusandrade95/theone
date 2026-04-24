# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-e27c412e3a274d66
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: Corte
Turn 2 assistant: Tudo certo, já ajustei para Corte. Qual dia lhe convém melhor?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo, já ajustei aqui. Qual horário seria melhor pra você?
Turn 4 user: 16h17
Turn 4 assistant: Ajustei o horário: pré-agendamento de Corte no dia 20 de abr às 16:17, tudo certo? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo de confirmação: Corte agendado para 20 de abril às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Tudo certo! Sua pré-reserva foi criada com sucesso.
```

## Failures

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
