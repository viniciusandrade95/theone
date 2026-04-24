# generated_i0003_02_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-d97874220a68412d
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 2 user: meu corte
Turn 2 assistant: Consigo te ajudar com corte. Queres saber o preço, ver detalhes ou já te ajudo a marcar?
Turn 3 user: 16h
Turn 3 assistant: Perfeito, ajustei para Corte. Qual dia fica melhor para você?
Turn 4 user: pode
Turn 4 assistant: Qual dia fica melhor para você?
```

## Failures

- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: unexpected RAG route
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected workflow reschedule_appointment, got book_appointment
- step 4: assertion_failure: expected workflow reschedule_appointment, got book_appointment

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
