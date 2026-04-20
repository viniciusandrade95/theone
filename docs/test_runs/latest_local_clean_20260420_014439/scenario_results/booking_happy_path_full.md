# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-094f927ca9f1408c
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: sim, pode confirmar
Turn 2 assistant: No studio, sobre confirmação: O pré-agendamento fica sujeito à confirmação humana final.
```

## Failures

- step 1: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=blocked
- step 1: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 2: assertion_failure: expected status completed, got response=ok workflow=None
- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: expected action_result.ok=True, got None
- step 2: assertion_failure: unexpected RAG route
- crm_verification_failure: expected matching appointment to exist

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[],\"total\":0,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 100
  },
  "reasons": [
    "expected matching appointment to exist"
  ],
  "status": "FAIL",
  "matched": [],
  "total_items": 0
}
```
