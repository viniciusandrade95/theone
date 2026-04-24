# generated_i0003_03_seed_cancellation_colloquial

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: não posso ir amanhã
Turn 1 assistant: 
Turn 2 user: cancela meu corte pfv
Turn 2 assistant: 
Turn 3 user: sim
Turn 3 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 1: assertion_failure: expected workflow cancel_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: assertion_failure: expected workflow cancel_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 3: assertion_failure: expected workflow cancel_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
