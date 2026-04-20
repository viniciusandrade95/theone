# reschedule_missing_time

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-81f545dea49d4c15
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: No studio, sobre remarcação: Se precisares remarcar, fazemos o possível para encontrar outro horário no mesmo dia ou na sequência.
```

## Failures

- step 1: assertion_failure: expected status collecting, got response=ok workflow=None
- step 1: assertion_failure: expected route workflow, got rag
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: expected slot new_date to be present
- step 1: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
