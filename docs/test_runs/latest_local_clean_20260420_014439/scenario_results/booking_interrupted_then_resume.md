# booking_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-ea2681fded73424e
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 18h
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: Qual o endereço mesmo?
Turn 2 assistant: Rua das Acácias, 45 - Sala 3. Há vagas rotativas na rua e estacionamento parceiro ao lado.
Turn 3 user: Beleza, pode continuar
Turn 3 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
```

## Failures

- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 3: assertion_failure: expected slot time to be present
- step 3: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
