# generated_i0002_02_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: 699d095e-02bb-4c4d-853e-fcbae6832ed8
- Session ID: s-aef60c464d874cbc
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Claro. Para eu sugerir horários, qual serviço você quer? Posso te ajudar com Corte, Barba ou Sobrancelha.
Turn 2 user: corte amanhã
Turn 2 assistant: Tenho Corte no dia 22 de abr anotado. Prefere de manhã, à tarde ou à noite para eu seguir com uma sugestão?
Turn 3 user: de tarde
Turn 3 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 22 de abr às 15:00. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 22 de abr às 15:00. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 5 user: ok
Turn 5 assistant: Beleza. Pré-reserva criada com sucesso.
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 4: heuristic_failure: Repeated date question

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
