# booking_happy_path_full

- Verdict: PASS
- Conversation ID: 04bdf486-5d82-47cb-8e27-5447c09b0a5d
- Session ID: s-bd7d9c1a937e498e
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 23 de abr às 16:17. Tudo certo por aqui? Posso encaminhar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Perfeito. Pré-agendamento registrado com sucesso. Pré-reserva criada com sucesso.
```

## Failures

- None

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[{\"id\":\"9ed7afcb-bf00-4ade-a55b-e32e41a5d1a2\",\"tenant_id\":\"1fefd101-f151-40a0-905c-ae3086cc0e49\",\"customer_id\":\"0f207289-4112-4db5-b181-9a4a735ab803\",\"customer_name\":\"Audit User\",\"location_id\":\"e7a7d4e0-9774-4de3-a4b2-e23f195bc731\",\"service_id\":\"6a99ea2d-e12c-455d-b68e-6dc75ec1e86e\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:35:26.443828\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:35:26\"},{\"id\":\"9cf34089-3b0a-4895-8db3-b266d0b7d3a7\",\"tenant_id\":\"1fefd101-f151-40a0-905c-ae3086cc0e49\",\"customer_id\":\"0f207289-4112-4db5-b181-9a4a735ab803\",\"customer_name\":\"Audit User\",\"location_id\":\"e7a7d4e0-9774-4de3-a4b2-e23f195bc731\",\"service_id\":\"6a99ea2d-e12c-455d-b68e-6dc75ec1e86e\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:35:18.758976\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:35:18\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "9ed7afcb-bf00-4ade-a55b-e32e41a5d1a2",
        "tenant_id": "1fefd101-f151-40a0-905c-ae3086cc0e49",
        "customer_id": "0f207289-4112-4db5-b181-9a4a735ab803",
        "customer_name": "Audit User",
        "location_id": "e7a7d4e0-9774-4de3-a4b2-e23f195bc731",
        "service_id": "6a99ea2d-e12c-455d-b68e-6dc75ec1e86e",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:35:26.443828",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:35:26"
      },
      {
        "id": "9cf34089-3b0a-4895-8db3-b266d0b7d3a7",
        "tenant_id": "1fefd101-f151-40a0-905c-ae3086cc0e49",
        "customer_id": "0f207289-4112-4db5-b181-9a4a735ab803",
        "customer_name": "Audit User",
        "location_id": "e7a7d4e0-9774-4de3-a4b2-e23f195bc731",
        "service_id": "6a99ea2d-e12c-455d-b68e-6dc75ec1e86e",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:35:18.758976",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:35:18"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 100
  },
  "reasons": [],
  "status": "PASS",
  "matched": [
    {
      "id": "9cf34089-3b0a-4895-8db3-b266d0b7d3a7",
      "tenant_id": "1fefd101-f151-40a0-905c-ae3086cc0e49",
      "customer_id": "0f207289-4112-4db5-b181-9a4a735ab803",
      "customer_name": "Audit User",
      "location_id": "e7a7d4e0-9774-4de3-a4b2-e23f195bc731",
      "service_id": "6a99ea2d-e12c-455d-b68e-6dc75ec1e86e",
      "service_name": "Corte",
      "starts_at": "2026-04-23T19:17:00",
      "ends_at": "2026-04-23T20:02:00",
      "status": "pending",
      "needs_confirmation": true,
      "cancelled_reason": null,
      "status_updated_at": "2026-04-22T21:35:18.758976",
      "notes": "created via assistant",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2026-04-22T21:35:18"
    }
  ],
  "total_items": 2
}
```
