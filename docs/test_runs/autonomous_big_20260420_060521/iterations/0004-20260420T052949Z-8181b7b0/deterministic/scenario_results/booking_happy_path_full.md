# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-0d5907d0c15e41e0
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 16:17. Tudo certo? Posso encaminhar para confirmação humana?
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
  "raw_body": "{\"items\":[{\"id\":\"855309e1-031a-4f69-801f-474b6f5fd642\",\"tenant_id\":\"907ee7f1-d7f2-421f-a9c7-466ba8dd93b7\",\"customer_id\":\"7f31dd8c-3d61-4952-8afb-3d1390c2d706\",\"customer_name\":\"Audit User\",\"location_id\":\"4e6b9e33-6e0a-4e83-879b-142ffa0baaf5\",\"service_id\":\"944cc6ff-4283-444f-bcc9-8281c5a5a9f6\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-21T15:00:00Z\",\"ends_at\":\"2026-04-21T15:30:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-20T03:15:25.530536Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-20T03:15:25.504444Z\"},{\"id\":\"58622dea-251c-4a51-b3e0-8fd3048a9c83\",\"tenant_id\":\"907ee7f1-d7f2-421f-a9c7-466ba8dd93b7\",\"customer_id\":\"7f31dd8c-3d61-4952-8afb-3d1390c2d706\",\"customer_name\":\"Audit User\",\"location_id\":\"4e6b9e33-6e0a-4e83-879b-142ffa0baaf5\",\"service_id\":\"944cc6ff-4283-444f-bcc9-8281c5a5a9f6\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-21T16:17:00Z\",\"ends_at\":\"2026-04-21T16:47:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-20T03:15:17.231833Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-20T03:15:17.190604Z\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "855309e1-031a-4f69-801f-474b6f5fd642",
        "tenant_id": "907ee7f1-d7f2-421f-a9c7-466ba8dd93b7",
        "customer_id": "7f31dd8c-3d61-4952-8afb-3d1390c2d706",
        "customer_name": "Audit User",
        "location_id": "4e6b9e33-6e0a-4e83-879b-142ffa0baaf5",
        "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
        "service_name": "Corte",
        "starts_at": "2026-04-21T15:00:00Z",
        "ends_at": "2026-04-21T15:30:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-20T03:15:25.530536Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-20T03:15:25.504444Z"
      },
      {
        "id": "58622dea-251c-4a51-b3e0-8fd3048a9c83",
        "tenant_id": "907ee7f1-d7f2-421f-a9c7-466ba8dd93b7",
        "customer_id": "7f31dd8c-3d61-4952-8afb-3d1390c2d706",
        "customer_name": "Audit User",
        "location_id": "4e6b9e33-6e0a-4e83-879b-142ffa0baaf5",
        "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
        "service_name": "Corte",
        "starts_at": "2026-04-21T16:17:00Z",
        "ends_at": "2026-04-21T16:47:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-20T03:15:17.231833Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-20T03:15:17.190604Z"
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
