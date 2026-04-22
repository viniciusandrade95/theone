# booking_happy_path_full

- Verdict: PARTIAL
- Conversation ID: 072696af-b920-4067-a16d-d128610abc28
- Session ID: s-ede827f28475423a
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
  "raw_body": "{\"items\":[{\"id\":\"f78260d8-1445-422f-8f4d-836d7c772ec7\",\"tenant_id\":\"647eca36-2f81-4850-b396-555228f56f4b\",\"customer_id\":\"7bc0bc8e-c7a6-42b3-8240-1cc2bc6f6a29\",\"customer_name\":\"Audit User\",\"location_id\":\"9d7b2862-d8b0-464f-a481-da84b07828ec\",\"service_id\":\"f34879c7-4eb9-4caf-842e-612bf1ea4094\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:39:11.509423\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:39:11\"},{\"id\":\"f5ef8bbf-7b14-44f5-9172-1ec1177e6be5\",\"tenant_id\":\"647eca36-2f81-4850-b396-555228f56f4b\",\"customer_id\":\"7bc0bc8e-c7a6-42b3-8240-1cc2bc6f6a29\",\"customer_name\":\"Audit User\",\"location_id\":\"9d7b2862-d8b0-464f-a481-da84b07828ec\",\"service_id\":\"f34879c7-4eb9-4caf-842e-612bf1ea4094\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:39:03.998471\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:39:03\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "f78260d8-1445-422f-8f4d-836d7c772ec7",
        "tenant_id": "647eca36-2f81-4850-b396-555228f56f4b",
        "customer_id": "7bc0bc8e-c7a6-42b3-8240-1cc2bc6f6a29",
        "customer_name": "Audit User",
        "location_id": "9d7b2862-d8b0-464f-a481-da84b07828ec",
        "service_id": "f34879c7-4eb9-4caf-842e-612bf1ea4094",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:39:11.509423",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:39:11"
      },
      {
        "id": "f5ef8bbf-7b14-44f5-9172-1ec1177e6be5",
        "tenant_id": "647eca36-2f81-4850-b396-555228f56f4b",
        "customer_id": "7bc0bc8e-c7a6-42b3-8240-1cc2bc6f6a29",
        "customer_name": "Audit User",
        "location_id": "9d7b2862-d8b0-464f-a481-da84b07828ec",
        "service_id": "f34879c7-4eb9-4caf-842e-612bf1ea4094",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:39:03.998471",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:39:03"
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
