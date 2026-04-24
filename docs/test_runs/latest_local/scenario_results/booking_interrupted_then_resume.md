# booking_interrupted_then_resume

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 18h
Turn 1 assistant: 
Turn 2 user: Qual o endereço mesmo?
Turn 2 assistant: 
Turn 3 user: Beleza, pode continuar
Turn 3 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- step 3: upstream_runtime_failure: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 3: assertion_failure: expected slot time to be present

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
