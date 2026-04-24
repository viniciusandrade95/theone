# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-5e1c1dd617cc4650
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: Infelizmente, a integração está temporariamente indisponível. Vou encaminhá-lo(a) para um atendente humano.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: A integração está temporariamente indisponível. Vou encaminhá-lo(a) para atendimento humano.
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
