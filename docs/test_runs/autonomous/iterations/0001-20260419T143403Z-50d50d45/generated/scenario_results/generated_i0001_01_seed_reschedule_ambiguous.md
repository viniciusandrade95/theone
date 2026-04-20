# generated_i0001_01_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-805443f494c048ea
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 2 user: meu corte
Turn 2 assistant: Perfeito, ajustei para Corte. Qual dia fica melhor para você?
Turn 3 user: 16h
Turn 3 assistant: Perfeito, ajustei isso por aqui. Qual dia fica melhor para você?
Turn 4 user: pode
Turn 4 assistant: Posso te ajudar com corte. Quer saber o preço, conferir detalhes ou já marcar?
```

## Failures

- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: unexpected RAG route
- step 2: assertion_failure: expected workflow reschedule_appointment, got book_appointment
- step 3: assertion_failure: expected workflow reschedule_appointment, got book_appointment
- step 4: assertion_failure: expected workflow reschedule_appointment, got None
- step 4: assertion_failure: unexpected RAG route
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
