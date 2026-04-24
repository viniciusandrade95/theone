# booking_user_changes_time_mid_flow

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-75e205bed5ba4c19
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: Na verdade muda para 16h17
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 3 user: sim
Turn 3 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
```

## Failures

- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: 16
- step 2: assertion_failure: expected slot service to be present
- step 2: assertion_failure: expected slot date to be present
- step 2: assertion_failure: expected slot time to be present
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected route workflow, got rag
- step 3: assertion_failure: expected workflow book_appointment, got None
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
