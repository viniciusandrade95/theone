# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: 699d095e-02bb-4c4d-853e-fcbae6832ed8
- Session ID: s-5a02859493c34587
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 23 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Perfeito. Pré-reserva criada com sucesso.
```

## Failures

- step 2: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- crm_verification_failure: expected matching appointment to exist

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[{\"id\":\"da443d00-e79d-4d15-80d0-97f932f1fccb\",\"tenant_id\":\"82e54494-d4c0-4529-be81-6a3180b4cdca\",\"customer_id\":\"a4edfd4e-9ede-4bc1-8055-805c81415eff\",\"customer_name\":\"Maria QA\",\"location_id\":\"71819b53-63ba-45f3-b860-bc56a5e8eb06\",\"service_id\":\"9b66b63d-9d5f-472a-a5bc-a594f78a0b5a\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00Z\",\"ends_at\":\"2026-04-23T18:45:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T03:00:03.075431Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T03:00:03.058870Z\"},{\"id\":\"b3f9e421-5236-4e7a-ac37-7e59f6c2ba08\",\"tenant_id\":\"82e54494-d4c0-4529-be81-6a3180b4cdca\",\"customer_id\":\"a4edfd4e-9ede-4bc1-8055-805c81415eff\",\"customer_name\":\"Maria QA\",\"location_id\":\"71819b53-63ba-45f3-b860-bc56a5e8eb06\",\"service_id\":\"9b66b63d-9d5f-472a-a5bc-a594f78a0b5a\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00Z\",\"ends_at\":\"2026-04-23T20:02:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T03:00:09.486178Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T03:00:09.466916Z\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "da443d00-e79d-4d15-80d0-97f932f1fccb",
        "tenant_id": "82e54494-d4c0-4529-be81-6a3180b4cdca",
        "customer_id": "a4edfd4e-9ede-4bc1-8055-805c81415eff",
        "customer_name": "Maria QA",
        "location_id": "71819b53-63ba-45f3-b860-bc56a5e8eb06",
        "service_id": "9b66b63d-9d5f-472a-a5bc-a594f78a0b5a",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00Z",
        "ends_at": "2026-04-23T18:45:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T03:00:03.075431Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T03:00:03.058870Z"
      },
      {
        "id": "b3f9e421-5236-4e7a-ac37-7e59f6c2ba08",
        "tenant_id": "82e54494-d4c0-4529-be81-6a3180b4cdca",
        "customer_id": "a4edfd4e-9ede-4bc1-8055-805c81415eff",
        "customer_name": "Maria QA",
        "location_id": "71819b53-63ba-45f3-b860-bc56a5e8eb06",
        "service_id": "9b66b63d-9d5f-472a-a5bc-a594f78a0b5a",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00Z",
        "ends_at": "2026-04-23T20:02:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T03:00:09.486178Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T03:00:09.466916Z"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 100
  },
  "reasons": [
    "expected matching appointment to exist"
  ],
  "status": "FAIL",
  "matched": [],
  "total_items": 2
}
```
