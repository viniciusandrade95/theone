# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-6ee14a601a9d4be3
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: Perfeito, ajustei para Corte. E qual horário você prefere?
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer o endereço, como chegar ou informação de estacionamento? Se quiser, depois a gente retoma a remarcação.
Turn 3 user: 16h17
Turn 3 assistant: Perfeito, ajustei o horário. Resumo para confirmação: remarcação de seu próximo agendamento para 21 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
```

## Failures

- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: assertion_failure: unexpected RAG route
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
