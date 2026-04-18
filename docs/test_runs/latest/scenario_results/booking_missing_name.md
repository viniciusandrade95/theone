# booking_missing_name

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h
Turn 1 assistant: 
Turn 2 user: sim
Turn 2 assistant: 
Turn 3 user: Audit User
Turn 3 assistant: 
```

## Failures

- step 1: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T143935Z-a6fbf12b-booking_missing_name-1"}
- step 1: expected status awaiting_confirmation, got response=None workflow=None
- step 1: expected route workflow, got None
- step 1: expected workflow book_appointment, got None
- step 1: expected slot service to be present
- step 1: expected slot date to be present
- step 1: expected slot time to be present
- step 2: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T143935Z-a6fbf12b-booking_missing_name-2"}
- step 2: expected route workflow, got None
- step 2: expected workflow book_appointment, got None
- step 2: reply missing expected text: nome
- step 3: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-20260418T143935Z-a6fbf12b-booking_missing_name-3"}
- step 3: expected route workflow, got None
- step 3: expected workflow book_appointment, got None
- step 3: reply missing expected text: telefone
- crm: expected no matching appointment, but found one

## CRM Verification

```json
{
  "status_code": 200,
  "raw_body": "{\"items\":[{\"id\":\"d2bcf69a-b277-4158-8b6f-4452452f8b1e\",\"tenant_id\":\"4cd335f6-00bc-482a-8d91-154a775bcb7b\",\"customer_id\":\"f8e19270-884d-431a-9347-ae5cd1e9cc20\",\"customer_name\":\"Audit User\",\"location_id\":\"6318247d-2b95-4cd2-8e3a-c5fe546957bc\",\"service_id\":\"944cc6ff-4283-444f-bcc9-8281c5a5a9f6\",\"service_name\":\"Corte (audit)\",\"starts_at\":\"2026-04-18T15:00:00Z\",\"ends_at\":\"2026-04-18T15:45:00Z\",\"status\":\"pending\",\"needs_confirmation\":true,\"cancelled_reason\":null,\"status_updated_at\":\"2026-04-17T21:19:55.706687Z\",\"notes\":\"audit prebook\",\"created_by_user_id\":null,\"updated_by_user_id\":null,\"created_at\":\"2026-04-17T21:19:54.267902Z\"}],\"total\":1,\"page\":1,\"page_size\":100}",
  "parsed_body": {
    "items": [
      {
        "id": "d2bcf69a-b277-4158-8b6f-4452452f8b1e",
        "tenant_id": "4cd335f6-00bc-482a-8d91-154a775bcb7b",
        "customer_id": "f8e19270-884d-431a-9347-ae5cd1e9cc20",
        "customer_name": "Audit User",
        "location_id": "6318247d-2b95-4cd2-8e3a-c5fe546957bc",
        "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
        "service_name": "Corte (audit)",
        "starts_at": "2026-04-18T15:00:00Z",
        "ends_at": "2026-04-18T15:45:00Z",
        "status": "pending",
        "needs_confirmation": true,
        "cancelled_reason": null,
        "status_updated_at": "2026-04-17T21:19:55.706687Z",
        "notes": "audit prebook",
        "created_by_user_id": null,
        "updated_by_user_id": null,
        "created_at": "2026-04-17T21:19:54.267902Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 100
  },
  "reasons": [
    "expected no matching appointment, but found one"
  ],
  "status": "FAIL",
  "matched": [
    {
      "id": "d2bcf69a-b277-4158-8b6f-4452452f8b1e",
      "tenant_id": "4cd335f6-00bc-482a-8d91-154a775bcb7b",
      "customer_id": "f8e19270-884d-431a-9347-ae5cd1e9cc20",
      "customer_name": "Audit User",
      "location_id": "6318247d-2b95-4cd2-8e3a-c5fe546957bc",
      "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
      "service_name": "Corte (audit)",
      "starts_at": "2026-04-18T15:00:00Z",
      "ends_at": "2026-04-18T15:45:00Z",
      "status": "pending",
      "needs_confirmation": true,
      "cancelled_reason": null,
      "status_updated_at": "2026-04-17T21:19:55.706687Z",
      "notes": "audit prebook",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2026-04-17T21:19:54.267902Z"
    }
  ],
  "total_items": 1
}
```
