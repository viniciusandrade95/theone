# booking_happy_path_full

- Verdict: PARTIAL
- Conversation ID: 08beb4da-01bf-4708-8bd6-f6af036333fe
- Session ID: s-aafa3c4ef81d4240
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
  "raw_body": "{\"items\":[{\"id\":\"90edd09f-ffc8-47a2-9550-1e163a8283f7\",\"tenant_id\":\"c0aa7c9e-cb43-40b2-9bd4-aefcb82c029b\",\"customer_id\":\"f8d2825e-f1e9-4491-9278-bb1420b58b9c\",\"customer_name\":\"Audit User\",\"location_id\":\"f35fc047-574a-4135-8fbc-4a4fbd75e8f8\",\"service_id\":\"e5290f21-5daf-46e8-8317-8d3fba13952a\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:46:22.340756\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:46:22\"},{\"id\":\"47c31100-193e-4c90-be85-4efe8c71d59a\",\"tenant_id\":\"c0aa7c9e-cb43-40b2-9bd4-aefcb82c029b\",\"customer_id\":\"f8d2825e-f1e9-4491-9278-bb1420b58b9c\",\"customer_name\":\"Audit User\",\"location_id\":\"f35fc047-574a-4135-8fbc-4a4fbd75e8f8\",\"service_id\":\"e5290f21-5daf-46e8-8317-8d3fba13952a\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:46:13.221107\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:46:13\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "90edd09f-ffc8-47a2-9550-1e163a8283f7",
        "tenant_id": "c0aa7c9e-cb43-40b2-9bd4-aefcb82c029b",
        "customer_id": "f8d2825e-f1e9-4491-9278-bb1420b58b9c",
        "customer_name": "Audit User",
        "location_id": "f35fc047-574a-4135-8fbc-4a4fbd75e8f8",
        "service_id": "e5290f21-5daf-46e8-8317-8d3fba13952a",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:46:22.340756",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:46:22"
      },
      {
        "id": "47c31100-193e-4c90-be85-4efe8c71d59a",
        "tenant_id": "c0aa7c9e-cb43-40b2-9bd4-aefcb82c029b",
        "customer_id": "f8d2825e-f1e9-4491-9278-bb1420b58b9c",
        "customer_name": "Audit User",
        "location_id": "f35fc047-574a-4135-8fbc-4a4fbd75e8f8",
        "service_id": "e5290f21-5daf-46e8-8317-8d3fba13952a",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:46:13.221107",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:46:13"
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
