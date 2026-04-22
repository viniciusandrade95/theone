# booking_happy_path_full

- Verdict: PARTIAL
- Conversation ID: 12bec883-354b-4ae4-a8e9-e3864b78b751
- Session ID: s-2d205bf5abb94ff9
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
  "raw_body": "{\"items\":[{\"id\":\"1506f156-8316-4968-804b-8d37b9cb9a13\",\"tenant_id\":\"f1f3731f-303a-4ad9-86b0-05e4635c92de\",\"customer_id\":\"a3f32555-99a3-42e2-9c6c-0037881532bb\",\"customer_name\":\"Audit User\",\"location_id\":\"83bc2e41-6e11-4602-ab39-616bb98ddec0\",\"service_id\":\"858573c8-8f99-4a58-b72b-f0d34a9070ee\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:14:01.753502\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:14:01\"},{\"id\":\"93db0c42-2883-4f01-9bc6-3c70babaaf19\",\"tenant_id\":\"f1f3731f-303a-4ad9-86b0-05e4635c92de\",\"customer_id\":\"a3f32555-99a3-42e2-9c6c-0037881532bb\",\"customer_name\":\"Audit User\",\"location_id\":\"83bc2e41-6e11-4602-ab39-616bb98ddec0\",\"service_id\":\"858573c8-8f99-4a58-b72b-f0d34a9070ee\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:13:54.018182\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:13:54\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "1506f156-8316-4968-804b-8d37b9cb9a13",
        "tenant_id": "f1f3731f-303a-4ad9-86b0-05e4635c92de",
        "customer_id": "a3f32555-99a3-42e2-9c6c-0037881532bb",
        "customer_name": "Audit User",
        "location_id": "83bc2e41-6e11-4602-ab39-616bb98ddec0",
        "service_id": "858573c8-8f99-4a58-b72b-f0d34a9070ee",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:14:01.753502",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:14:01"
      },
      {
        "id": "93db0c42-2883-4f01-9bc6-3c70babaaf19",
        "tenant_id": "f1f3731f-303a-4ad9-86b0-05e4635c92de",
        "customer_id": "a3f32555-99a3-42e2-9c6c-0037881532bb",
        "customer_name": "Audit User",
        "location_id": "83bc2e41-6e11-4602-ab39-616bb98ddec0",
        "service_id": "858573c8-8f99-4a58-b72b-f0d34a9070ee",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:13:54.018182",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:13:54"
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
