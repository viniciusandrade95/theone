# generated_i0006_08_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-5f819acabbf54841
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Qual serviço você quer? Posso te ajudar com Corte.
Turn 2 user: corte amanhã
Turn 2 assistant: Perfeito, ajustei para Corte. Que horário te atende melhor?
Turn 3 user: de tarde
Turn 3 assistant: Encontrei mais de um agendamento possível. Informe a referência ou horário do agendamento que deseja remarcar.
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Perfeito, ajustei isso por aqui. Que horário te atende melhor?
Turn 5 user: ok
Turn 5 assistant: Que horário te atende melhor?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 4: heuristic_failure: Repeated time question
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
