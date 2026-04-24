# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-2035b73604cb4443
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 20 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Perfeito. booking.service_id is invalid or inactive
```

## Failures

- step 2: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 2: assertion_failure: expected action_result.ok=True, got False
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
