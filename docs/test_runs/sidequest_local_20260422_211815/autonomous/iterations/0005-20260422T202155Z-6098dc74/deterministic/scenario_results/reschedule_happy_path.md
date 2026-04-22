# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: 85eb3658-2e79-4043-b982-39f8ff5177df
- Session ID: s-1ce4c167e0ee4ab8
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: remarcação de seu próximo agendamento para 23 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Encontrei mais de um agendamento possível. Informe a referência ou horário do agendamento que deseja remarcar.
```

## Failures

- step 2: assertion_failure: expected status completed, got response=ok workflow=awaiting_target_reference
- step 2: assertion_failure: reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- step 2: heuristic_failure: Slot loss detected: time

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
