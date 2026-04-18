# booking_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-6bfb93f927614a43
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 18h
Turn 1 assistant: Tudo bem, alterei para Corte e pre‑agendado em 19 de abr às 18:00. Posso encaminhar para confirmação humana?
Turn 2 user: Qual o endereço mesmo?
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer o endereço, como chegar ou informação de estacionamento? Se quiser, depois a gente retoma o agendamento.
Turn 3 user: Beleza, pode continuar
Turn 3 assistant: Antes de confirmar, poderia me informar o nome do cliente para este agendamento?
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
