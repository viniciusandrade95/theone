# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: 699d095e-02bb-4c4d-853e-fcbae6832ed8
- Session ID: s-060e53bea1be4bd6
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: Perfeito, ajustei para Corte. E qual horário você prefere?
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: Rua das Palmeiras, 123 - Centro. Há estacionamento conveniado na mesma quadra. Se quiser, depois a gente retoma a remarcação.
Turn 3 user: 16h17
Turn 3 assistant: Perfeito, ajustei o horário. Resumo para confirmação: remarcação de seu próximo agendamento para 22 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
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
