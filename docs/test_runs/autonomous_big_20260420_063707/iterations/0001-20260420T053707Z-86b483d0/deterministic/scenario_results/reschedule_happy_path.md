# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-955b7e80342f40dd
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: Perfeito, ajustei para Corte. Você tem a referência do agendamento ou a data?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Falta so me dizer booking_ref para seguir.
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 1: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 2: assertion_failure: expected status completed, got response=ok workflow=collecting
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
