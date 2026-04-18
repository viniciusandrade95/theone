# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-8236b18a261a4ead
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Resumo para confirmação: pré‑agendamento de Corte no dia 19 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: Corte
Turn 2 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 19 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo, ajustei a data: pré-agendamento de Corte em 19 de abr às 16:17. Posso enviar para confirmação humana?
Turn 4 user: 16h17
Turn 4 assistant: Perfeito, ajustei o horário. Confirma: pré‑agendamento de Corte no dia 19 de abr às 16:17? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Entendido — já pedi um atendente humano. A nossa equipa vai entrar em contacto em breve.
```

## Failures

- step 1: assertion_failure: reply missing expected text: serviço
- step 5: assertion_failure: expected workflow book_appointment, got handoff_to_human
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
