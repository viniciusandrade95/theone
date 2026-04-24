# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-86c951375825420d
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: Corte
Turn 2 assistant: Tudo certo, mudei para Corte. Qual dia seria melhor pra você?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo, já ajustei. Qual horário funciona melhor pra você?
Turn 4 user: 16h17
Turn 4 assistant: Tudo bem, ajustei o horário: pré‑agendamento de Corte em 20 de abr às 16:17. Posso enviar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo: pré‑agendamento de Corte em 20 de abril às 16:17. Tudo certo? Posso enviar para confirmação humana?
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Perfeito. Pré-reserva criada com sucesso.
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
