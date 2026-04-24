# faq_then_booking

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Tem vaga amanhã?
Turn 1 assistant: 
Turn 2 user: Quero corte às 16h17 para Audit User, telefone 11999998888
Turn 2 assistant: 
Turn 3 user: sim pode confirmar
Turn 3 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: expected slot service to be present
- step 2: assertion_failure: expected slot time to be present
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 3: assertion_failure: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
