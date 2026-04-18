# booking_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-6d1b58d43fc240df
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 18h
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 19 de abr às 18:00, tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: Qual o endereço mesmo?
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer o endereço, como chegar ou informação de estacionamento? Se quiser, depois a gente retoma o agendamento.
Turn 3 user: Beleza, pode continuar
Turn 3 assistant: Antes de confirmar, qual o nome do cliente para esse agendamento?
```

## Failures

- step 2: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
