# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-9715d9e735a14e99
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: Perfeito, ajustei para Corte. E qual horário você prefere?
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer o endereço, como chegar ou informação de estacionamento? Se quiser, depois a gente retoma a remarcação.
Turn 3 user: 16h17
Turn 3 assistant: Beleza, vamos ajustar a referência. Você tem a referência do agendamento ou a data?
```

## Failures

- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 3: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
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
