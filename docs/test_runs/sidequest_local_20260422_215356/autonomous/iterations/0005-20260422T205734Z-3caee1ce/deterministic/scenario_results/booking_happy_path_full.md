# booking_happy_path_full

- Verdict: PARTIAL
- Conversation ID: 4cb846c1-82a7-474f-9bee-fdb705ace4ea
- Session ID: s-67f7e839c2524054
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 23 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Perfeito. Pré-agendamento registrado com sucesso. Pré-reserva criada com sucesso.
```

## Failures

- crm_verification_failure: expected matching appointment to exist

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[{\"id\":\"e3722703-0ac6-4924-bda5-de6b8ff4f49e\",\"tenant_id\":\"1bd1fced-8f18-4cc4-b7e5-b32b9401246a\",\"customer_id\":\"2b65eb95-c4b0-430c-ab14-db74b9221b03\",\"customer_name\":\"Audit User\",\"location_id\":\"3ed09145-c58f-49aa-be0c-5b63d7bd3ca7\",\"service_id\":\"990ec4eb-a031-450f-81ce-4b6cc2c465be\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:54:12.756118\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:54:12\"},{\"id\":\"99f2c489-4a5a-4c03-9c57-6e2790320265\",\"tenant_id\":\"1bd1fced-8f18-4cc4-b7e5-b32b9401246a\",\"customer_id\":\"2b65eb95-c4b0-430c-ab14-db74b9221b03\",\"customer_name\":\"Audit User\",\"location_id\":\"3ed09145-c58f-49aa-be0c-5b63d7bd3ca7\",\"service_id\":\"990ec4eb-a031-450f-81ce-4b6cc2c465be\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:54:05.172362\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:54:05\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "e3722703-0ac6-4924-bda5-de6b8ff4f49e",
        "tenant_id": "1bd1fced-8f18-4cc4-b7e5-b32b9401246a",
        "customer_id": "2b65eb95-c4b0-430c-ab14-db74b9221b03",
        "customer_name": "Audit User",
        "location_id": "3ed09145-c58f-49aa-be0c-5b63d7bd3ca7",
        "service_id": "990ec4eb-a031-450f-81ce-4b6cc2c465be",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:54:12.756118",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:54:12"
      },
      {
        "id": "99f2c489-4a5a-4c03-9c57-6e2790320265",
        "tenant_id": "1bd1fced-8f18-4cc4-b7e5-b32b9401246a",
        "customer_id": "2b65eb95-c4b0-430c-ab14-db74b9221b03",
        "customer_name": "Audit User",
        "location_id": "3ed09145-c58f-49aa-be0c-5b63d7bd3ca7",
        "service_id": "990ec4eb-a031-450f-81ce-4b6cc2c465be",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:54:05.172362",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:54:05"
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
