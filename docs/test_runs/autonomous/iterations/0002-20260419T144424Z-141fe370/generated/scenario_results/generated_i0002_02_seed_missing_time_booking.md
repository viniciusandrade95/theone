# generated_i0002_02_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-09c83d2ef79d4fba
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: corte amanhã
Turn 2 assistant: Perfeito, ajustei para Corte. Que horário te atende melhor?
Turn 3 user: de tarde
Turn 3 assistant: Consigo te ajudar com corte. Queres saber o preço, ver detalhes ou já te ajudo a marcar?
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Perfeito, ajustei isso por aqui. Que horário te atende melhor?
Turn 5 user: ok
Turn 5 assistant: Qual horário funciona melhor pra você?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: unexpected RAG route
- step 3: heuristic_failure: RAG route during operational flow
- step 5: heuristic_failure: Repeated time question
- heuristic_failure: Expected final status awaiting_confirmation, got collecting

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
