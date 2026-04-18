# booking_with_colloquial_ptbr

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-8236b18a261a4ead
- Judge: DISABLED

## Transcript

```text
Turn 1 user: opa, queria corta o cabelo amanha la pras 4 e 17 da tarde
Turn 1 assistant: Entendido — já pedi um atendente humano. A nossa equipa vai entrar em contacto em breve.
Turn 2 user: meu nome é Audit User e o zap é 11999998888
Turn 2 assistant: Entendido — já pedi um atendente humano. A nossa equipa vai entrar em contacto em breve.
Turn 3 user: isso, manda bala
Turn 3 assistant: Entendido — já pedi um atendente humano. A nossa equipa vai entrar em contacto em breve.
```

## Failures

- step 1: assertion_failure: expected workflow book_appointment, got handoff_to_human
- step 2: assertion_failure: expected workflow book_appointment, got handoff_to_human
- step 2: assertion_failure: reply missing expected text: confirmar
- step 3: assertion_failure: expected workflow book_appointment, got handoff_to_human

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
