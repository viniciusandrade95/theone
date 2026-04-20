# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-33c8356509be4195
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: No studio, sobre remarcação: Se precisares remarcar, fazemos o possível para encontrar outro horário no mesmo dia ou na sequência.
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: Rua das Acácias, 45 - Sala 3. Há vagas rotativas na rua e estacionamento parceiro ao lado.
Turn 3 user: 16h17
Turn 3 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
```

## Failures

- step 1: assertion_failure: expected status collecting, got response=ok workflow=None
- step 1: assertion_failure: expected route workflow, got rag
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: expected slot new_date to be present
- step 1: assertion_failure: unexpected RAG route
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=None
- step 3: assertion_failure: expected route workflow, got rag
- step 3: assertion_failure: expected workflow reschedule_appointment, got None
- step 3: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 3: assertion_failure: expected slot new_date to be present
- step 3: assertion_failure: expected slot new_time to be present
- step 3: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
