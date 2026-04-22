# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: 85eb3658-2e79-4043-b982-39f8ff5177df
- Session ID: s-a1914499aa94476c
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
  "raw_body": "{\"items\":[{\"id\":\"a0548686-f000-4ee7-b0b1-7510f0f061ae\",\"tenant_id\":\"e2d2743a-4fce-45e7-af58-1b67e15d4fce\",\"customer_id\":\"e44b17a1-ad06-412f-8efc-6e0ecc41261d\",\"customer_name\":\"Vinicius\",\"location_id\":\"f79b1622-9235-40d4-b3d5-df1537b2649a\",\"service_id\":\"a686e3a6-6720-4cb5-9be4-dce8d45b8364\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T18:00:00\",\"ends_at\":\"2026-04-23T18:45:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:15:39.611990\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:15:39\"},{\"id\":\"a7228f8e-9bea-49d3-a766-3b5e4c33bf64\",\"tenant_id\":\"e2d2743a-4fce-45e7-af58-1b67e15d4fce\",\"customer_id\":\"3d682e8a-436b-4196-860c-62210f9c4f80\",\"customer_name\":\"Audit User\",\"location_id\":\"f79b1622-9235-40d4-b3d5-df1537b2649a\",\"service_id\":\"a686e3a6-6720-4cb5-9be4-dce8d45b8364\",\"service_name\":\"Corte\",\"starts_at\":\"2026-04-23T19:17:00\",\"ends_at\":\"2026-04-23T20:02:00\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-22T20:15:35.867103\",\"notes\":\"created via assistant\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-22T20:15:35\"}],\"total\":2,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "a0548686-f000-4ee7-b0b1-7510f0f061ae",
        "tenant_id": "e2d2743a-4fce-45e7-af58-1b67e15d4fce",
        "customer_id": "e44b17a1-ad06-412f-8efc-6e0ecc41261d",
        "customer_name": "Vinicius",
        "location_id": "f79b1622-9235-40d4-b3d5-df1537b2649a",
        "service_id": "a686e3a6-6720-4cb5-9be4-dce8d45b8364",
        "service_name": "Corte",
        "starts_at": "2026-04-23T18:00:00",
        "ends_at": "2026-04-23T18:45:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:15:39.611990",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:15:39"
      },
      {
        "id": "a7228f8e-9bea-49d3-a766-3b5e4c33bf64",
        "tenant_id": "e2d2743a-4fce-45e7-af58-1b67e15d4fce",
        "customer_id": "3d682e8a-436b-4196-860c-62210f9c4f80",
        "customer_name": "Audit User",
        "location_id": "f79b1622-9235-40d4-b3d5-df1537b2649a",
        "service_id": "a686e3a6-6720-4cb5-9be4-dce8d45b8364",
        "service_name": "Corte",
        "starts_at": "2026-04-23T19:17:00",
        "ends_at": "2026-04-23T20:02:00",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-22T20:15:35.867103",
        "notes": "created via assistant",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-22T20:15:35"
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
