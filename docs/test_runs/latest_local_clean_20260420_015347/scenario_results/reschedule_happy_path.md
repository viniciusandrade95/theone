# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-8cd882e568424917
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: Na barbearia, sobre remarcação: Cortes podem ser remarcados com até 2h de antecedência, conforme disponibilidade da barbearia.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Na barbearia, sobre confirmação: Os agendamentos passam por confirmação humana antes de fechar definitivamente.
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=None
- step 1: assertion_failure: expected route workflow, got rag
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: expected slot new_date to be present
- step 1: assertion_failure: expected slot new_time to be present
- step 1: assertion_failure: unexpected RAG route
- step 2: assertion_failure: expected status completed, got response=ok workflow=None
- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- step 2: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
