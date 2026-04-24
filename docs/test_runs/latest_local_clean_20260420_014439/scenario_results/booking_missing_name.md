# booking_missing_name

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-17972b8ede0d4f83
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: sim
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 3 user: Audit User
Turn 3 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 4 user: pode confirmar
Turn 4 assistant: No studio, sobre confirmação: O pré-agendamento fica sujeito à confirmação humana final.
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=blocked
- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: nome
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=None
- step 3: assertion_failure: expected route workflow, got rag
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 3: assertion_failure: expected slot time to be present
- step 3: assertion_failure: expected slot customer_name to be present
- step 3: assertion_failure: unexpected RAG route
- step 4: assertion_failure: expected status collecting, got response=ok workflow=None
- step 4: assertion_failure: expected route workflow, got rag
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 4: assertion_failure: reply missing expected text: telefone
- step 4: assertion_failure: expected action_result.missing_customer_phone=True, got None
- step 4: assertion_failure: unexpected RAG route

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
