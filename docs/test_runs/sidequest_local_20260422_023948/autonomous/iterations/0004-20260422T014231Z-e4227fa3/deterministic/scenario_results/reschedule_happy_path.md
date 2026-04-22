# reschedule_happy_path

- Verdict: FAIL
- Conversation ID: 699d095e-02bb-4c4d-853e-fcbae6832ed8
- Session ID: s-27b7cfb0deeb4f9c
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã às 16h17
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: remarcação de seu próximo agendamento para 22 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
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
