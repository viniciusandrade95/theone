# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-51e935b9a7014d11
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você procura? Posso ajudar com Corte.
Turn 2 user: Corte
Turn 2 assistant: Ótimo! Ajustei para Corte. Qual dia fica melhor para você?
Turn 3 user: amanhã
Turn 3 assistant: Tudo certo, ajustei aqui. Qual horário fica melhor pra você?
Turn 4 user: 16h17
Turn 4 assistant: Perfeito, ajustei o horário: pré‑agendamento de Corte no dia 19 de abr às 16:17, tudo certo? Posso encaminhar para confirmação humana?
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Resumo para confirmação: pré-agendamento de Corte no dia 19 de abr às 16:17, tudo certo? Posso encaminhar para confirmação humana?
```

## Failures

- step 5: assertion_failure: expected slot customer_name to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
