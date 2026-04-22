# generated_i0003_01_seed_colloquial_fragmented_booking

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: mano queria cortar amanhã
Turn 1 assistant: 
Turn 2 user: pode ser corte
Turn 2 assistant: 
Turn 3 user: 16h? nao, 17h melhor
Turn 3 assistant: 
Turn 4 user: Audit User, 11999998888
Turn 4 assistant: 
Turn 5 user: sim
Turn 5 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T034942Z-aef20d8a-generated_i0003_01_seed_colloquial_fragmented_booking-1"}
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T034942Z-aef20d8a-generated_i0003_01_seed_colloquial_fragmented_booking-2"}
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T034942Z-aef20d8a-generated_i0003_01_seed_colloquial_fragmented_booking-3"}
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T034942Z-aef20d8a-generated_i0003_01_seed_colloquial_fragmented_booking-4"}
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 5: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"autonomous-eval-generated-20260422T034942Z-aef20d8a-generated_i0003_01_seed_colloquial_fragmented_booking-5"}
- step 5: assertion_failure: expected workflow book_appointment, got None
- heuristic_failure: Expected final status completed, got unknown

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
