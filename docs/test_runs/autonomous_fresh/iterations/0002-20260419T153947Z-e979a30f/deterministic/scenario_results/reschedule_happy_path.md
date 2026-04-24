# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-0020370536504fb0
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: A integração está temporariamente indisponível. Vou encaminhar seu caso para atendimento humano.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Consigo te ajudar com corte. Queres saber o preço, ver detalhes ou já te ajudo a marcar?
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 1: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 2: assertion_failure: expected status completed, got response=ok workflow=None
- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- step 2: assertion_failure: unexpected RAG route
- step 2: heuristic_failure: RAG route during operational flow

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
