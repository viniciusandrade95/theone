# reschedule_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero remarcar meu corte para amanhã
Turn 1 assistant: 
Turn 2 user: qual o endereço mesmo?
Turn 2 assistant: 
Turn 3 user: 16h17
Turn 3 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 1: assertion_failure: expected status collecting, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 1: assertion_failure: expected slot new_date to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 3: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 3: assertion_failure: expected route workflow, got None
- step 3: assertion_failure: expected workflow reschedule_appointment, got None
- step 3: assertion_failure: reply missing any expected text: remarcação, confirmar, confirmação
- step 3: assertion_failure: expected slot new_date to be present
- step 3: assertion_failure: expected slot new_time to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
