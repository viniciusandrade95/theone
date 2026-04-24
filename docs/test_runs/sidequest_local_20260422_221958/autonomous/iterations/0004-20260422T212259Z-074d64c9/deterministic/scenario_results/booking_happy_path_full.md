# booking_happy_path_full

- Verdict: PASS
- Conversation ID: 12419671-5f84-40e8-a133-0a0dff7892a9
- Session ID: s-b0b29c750acd47dc
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
  "raw_body": "{\"items\":[{\"id\":\"cda0eb15-d817-4a16-9bd4-6a63789f2e9b\",\"tenant_id\":\"a40b8ff1-1d3a-459b-b3e9-04e17f9fc170\",\"customer_id\":\"41b2dcdb-128e-4b31-b2f2-a313245595f1\",\"customer_name\":\"Audit User\",\"location_id\":\"16e2b4c1-c19e-479d-845a-2af856d9afac\",\"service_id\":\"88b80f91-2a84-49d3-9186-b3bd9df56bb9\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:20:20.026363\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:20:20\"},{\"id\":\"d1dedd06-95e7-4e19-8d3a-3b53aa6557b9\",\"tenant_id\":\"a40b8ff1-1d3a-459b-b3e9-04e17f9fc170\",\"customer_id\":\"41b2dcdb-128e-4b31-b2f2-a313245595f1\",\"customer_name\":\"Audit User\",\"location_id\":\"16e2b4c1-c19e-479d-845a-2af856d9afac\",\"service_id\":\"88b80f91-2a84-49d3-9186-b3bd9df56bb9\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T21:20:10.559990\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T21:20:10\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "cda0eb15-d817-4a16-9bd4-6a63789f2e9b",
        "tenant_id": "a40b8ff1-1d3a-459b-b3e9-04e17f9fc170",
        "customer_id": "41b2dcdb-128e-4b31-b2f2-a313245595f1",
        "customer_name": "Audit User",
        "location_id": "16e2b4c1-c19e-479d-845a-2af856d9afac",
        "service_id": "88b80f91-2a84-49d3-9186-b3bd9df56bb9",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:20:20.026363",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:20:20"
      },
      {
        "id": "d1dedd06-95e7-4e19-8d3a-3b53aa6557b9",
        "tenant_id": "a40b8ff1-1d3a-459b-b3e9-04e17f9fc170",
        "customer_id": "41b2dcdb-128e-4b31-b2f2-a313245595f1",
        "customer_name": "Audit User",
        "location_id": "16e2b4c1-c19e-479d-845a-2af856d9afac",
        "service_id": "88b80f91-2a84-49d3-9186-b3bd9df56bb9",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T21:20:10.559990",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T21:20:10"
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
      "id": "d1dedd06-95e7-4e19-8d3a-3b53aa6557b9",
      "tenant_id": "a40b8ff1-1d3a-459b-b3e9-04e17f9fc170",
      "customer_id": "41b2dcdb-128e-4b31-b2f2-a313245595f1",
      "customer_name": "Audit User",
      "location_id": "16e2b4c1-c19e-479d-845a-2af856d9afac",
      "service_id": "88b80f91-2a84-49d3-9186-b3bd9df56bb9",
      "service_name": "Corte",
      "starts_at": "2026-04-23T19:17:00",
      "ends_at": "2026-04-23T20:02:00",
      "status": "pending",
      "needs_confirmation": true,
      "cancelled_reason": null,
      "status_updated_at": "2026-04-22T21:20:10.559990",
      "notes": "created via assistant",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2026-04-22T21:20:10"
    }
  ],
  "total_items": 2
}
```
