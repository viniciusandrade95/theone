# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: 
Turn 2 user: sim, pode confirmar
Turn 2 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 0: 
- step 1: upstream_runtime_failure: response body is not a JSON object
- step 1: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: reply missing expected text: confirmar
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 0: 
- step 2: upstream_runtime_failure: response body is not a JSON object
- step 2: assertion_failure: expected status completed, got response=None workflow=None
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: registr
- step 2: assertion_failure: expected action_result.ok=True, got None
- crm_verification_failure: expected matching appointment to exist

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
    "expected matching appointment to exist"
  ],
  "status": "FAIL",
  "matched": [],
  "total_items": 1
}
```
