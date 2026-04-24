# generated_i0002_02_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: 
Turn 2 user: corte amanhã
Turn 2 assistant: 
Turn 3 user: de tarde
Turn 3 assistant: 
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: 
Turn 5 user: ok
Turn 5 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 5: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 5: assertion_failure: expected workflow book_appointment, got None
- heuristic_failure: Expected final status awaiting_confirmation, got unknown

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
