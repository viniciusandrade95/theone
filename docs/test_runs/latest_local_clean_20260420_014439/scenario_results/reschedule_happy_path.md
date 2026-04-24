# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-a2ae48b3a7c6404e
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: No studio, sobre remarcação: Se precisares remarcar, fazemos o possível para encontrar outro horário no mesmo dia ou na sequência.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: No studio, sobre confirmação: O pré-agendamento fica sujeito à confirmação humana final.
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
