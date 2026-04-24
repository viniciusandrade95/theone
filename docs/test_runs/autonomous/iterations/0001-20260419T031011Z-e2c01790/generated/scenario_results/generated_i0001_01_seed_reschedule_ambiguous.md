# generated_i0001_01_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-d6e36e115fc34e2f
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: Perfeito, ajustei para Pra. Qual nova data funciona melhor para você?
Turn 2 user: meu corte
Turn 2 assistant: Tudo certo, já mudei para Corte. Qual data você prefere?
Turn 3 user: 16h
Turn 3 assistant: Tudo bem, vamos ajustar a data. Qual nova data funciona melhor para você?
Turn 4 user: pode
Turn 4 assistant: Posso te ajudar com o corte. Quer saber o preço, ver detalhes ou já marcar?
```

## Failures

- step 4: assertion_failure: expected workflow reschedule_appointment, got None
- step 4: assertion_failure: unexpected RAG route
- step 3: heuristic_failure: Repeated date question
- step 4: heuristic_failure: RAG route during operational flow

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
