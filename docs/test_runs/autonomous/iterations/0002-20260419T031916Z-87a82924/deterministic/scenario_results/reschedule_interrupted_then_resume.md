# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-f68bc24a60d94a69
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: Tudo certo, ajustei para Corte. Qual horário você prefere?
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer o endereço, como chegar ou informação de estacionamento? Se quiser, depois a gente retoma a remarcação.
Turn 3 user: 16h17
Turn 3 assistant: A integração está fora do ar no momento. Vou encaminhá-lo(a) para um atendente humano.
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
