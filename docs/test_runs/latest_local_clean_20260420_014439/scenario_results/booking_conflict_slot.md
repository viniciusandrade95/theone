# booking_conflict_slot

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-8a22238a6b8e4bbc
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: sim
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
```

## Failures

- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow book_appointment, got None
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
