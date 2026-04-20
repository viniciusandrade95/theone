# generated_i0001_10_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-9cfe4581cb0249af
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: corte amanhã
Turn 2 assistant: Perfeito, ajustei para Corte. Que horário te atende melhor?
Turn 3 user: de tarde
Turn 3 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 15:00. Tudo certo? Posso encaminhar para confirmação humana?
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 15:00. Tudo certo? Posso encaminhar para confirmação humana?
Turn 5 user: ok
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 15:00. Tudo certo? Posso encaminhar para confirmação humana?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 5: heuristic_failure: Repeated date question

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
