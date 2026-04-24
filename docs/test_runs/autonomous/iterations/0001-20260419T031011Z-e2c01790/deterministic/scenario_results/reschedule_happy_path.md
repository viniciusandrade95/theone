# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-4b3172e671c34c0c
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: A integração está temporariamente indisponível. Vou encaminhar você para atendimento humano.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo, posso encaminhar para confirmação humana?
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 1: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 2: assertion_failure: expected status completed, got response=ok workflow=awaiting_confirmation
- step 2: assertion_failure: expected workflow reschedule_appointment, got book_appointment
- step 2: assertion_failure: reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
