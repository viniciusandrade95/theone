# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-9b90b2f62d1d41aa
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: Ótimo, mudei para Corte. Resumo: pré‑agendamento de Corte no dia 20 de abr às 16:17. Tudo certo e posso enviar para confirmação humana?
Turn 2 user: sim, pode confirmar
Turn 2 assistant: Tudo certo! A pré-reserva foi criada com sucesso.
```

## Failures

- step 2: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- crm_verification_failure: expected matching appointment to exist

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[{\"id\":\"01b9c4b9-f72d-4d02-a66f-cef4874b412a\",\"tenant_id\":\"4cd335f6-00bc-482a-8d91-154a775bcb7b\",\"customer_id\":\"bd288326-fb40-45d1-956b-a5f4069be575\",\"customer_name\":\"Audit User\",\"location_id\":\"6318247d-2b95-4cd2-8e3a-c5fe546957bc\",\"service_id\":\"944cc6ff-4283-444f-bcc9-8281c5a5a9f6\",\"service_name\":\"Corte (audit)\",\"starts_at\":\"2026-04-20T15:00:00Z\",\"ends_at\":\"2026-04-20T15:45:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-19T03:11:51.027524Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-19T03:11:49.822788Z\"},{\"id\":\"7f93d32e-ba10-43e1-8859-a0b792691586\",\"tenant_id\":\"4cd335f6-00bc-482a-8d91-154a775bcb7b\",\"customer_id\":\"bd288326-fb40-45d1-956b-a5f4069be575\",\"customer_name\":\"Audit User\",\"location_id\":\"6318247d-2b95-4cd2-8e3a-c5fe546957bc\",\"service_id\":\"944cc6ff-4283-444f-bcc9-8281c5a5a9f6\",\"service_name\":\"Corte (audit)\",\"starts_at\":\"2026-04-20T16:17:00Z\",\"ends_at\":\"2026-04-20T17:02:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-19T03:00:39.845588Z\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-19T03:00:38.694465Z\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "01b9c4b9-f72d-4d02-a66f-cef4874b412a",
        "tenant_id": "4cd335f6-00bc-482a-8d91-154a775bcb7b",
        "customer_id": "bd288326-fb40-45d1-956b-a5f4069be575",
        "customer_name": "Audit User",
        "location_id": "6318247d-2b95-4cd2-8e3a-c5fe546957bc",
        "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
        "service_name": "Corte (audit)",
        "starts_at": "2026-04-20T15:00:00Z",
        "ends_at": "2026-04-20T15:45:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-19T03:11:51.027524Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-19T03:11:49.822788Z"
      },
      {
        "id": "7f93d32e-ba10-43e1-8859-a0b792691586",
        "tenant_id": "4cd335f6-00bc-482a-8d91-154a775bcb7b",
        "customer_id": "bd288326-fb40-45d1-956b-a5f4069be575",
        "customer_name": "Audit User",
        "location_id": "6318247d-2b95-4cd2-8e3a-c5fe546957bc",
        "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
        "service_name": "Corte (audit)",
        "starts_at": "2026-04-20T16:17:00Z",
        "ends_at": "2026-04-20T17:02:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-19T03:00:39.845588Z",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-19T03:00:38.694465Z"
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
