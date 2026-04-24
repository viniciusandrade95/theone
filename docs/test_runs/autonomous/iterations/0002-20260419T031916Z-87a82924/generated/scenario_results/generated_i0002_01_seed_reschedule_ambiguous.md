# generated_i0002_01_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-a5ed45ce56934433
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: Tudo certo, ajustei para Pra. Qual nova data funciona melhor para você?
Turn 2 user: meu corte
Turn 2 assistant: Tudo certo, já alterei para Corte. Em que data nova você prefere?
Turn 3 user: 16h
Turn 3 assistant: Ótimo, vamos ajustar a data. Qual nova data funciona melhor para você?
Turn 4 user: pode
Turn 4 assistant: Posso te ajudar com o corte. Quer saber o preço, ver detalhes ou marcar já?
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
