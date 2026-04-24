# generated_i0001_02_seed_cancellation_colloquial

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

- step 1: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- step 1: assertion_failure: expected workflow cancel_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- step 2: assertion_failure: expected workflow cancel_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
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
