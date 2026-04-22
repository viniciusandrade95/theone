# generated_i0004_04_seed_reschedule_ambiguous

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: da pra mudar pra sexta?
Turn 1 assistant: 
Turn 2 user: meu corte
Turn 2 assistant: 
Turn 3 user: 16h
Turn 3 assistant: 
Turn 4 user: pode
Turn 4 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T035024Z-80d99b2c-generated_i0004_04_seed_reschedule_ambiguous-1"}
- step 1: assertion_failure: expected workflow reschedule_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T035024Z-80d99b2c-generated_i0004_04_seed_reschedule_ambiguous-2"}
- step 2: assertion_failure: expected workflow reschedule_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T035024Z-80d99b2c-generated_i0004_04_seed_reschedule_ambiguous-3"}
- step 3: assertion_failure: expected workflow reschedule_appointment, got None
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T035024Z-80d99b2c-generated_i0004_04_seed_reschedule_ambiguous-4"}
- step 4: assertion_failure: expected workflow reschedule_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
