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
Turn 4 user: pode confirmar
Turn 4 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172211Z-27ede721-booking_missing_name-1"}
- step 1: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172211Z-27ede721-booking_missing_name-2"}
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: nome
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172211Z-27ede721-booking_missing_name-3"}
- step 3: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 3: assertion_failure: expected route workflow, got None
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 3: assertion_failure: expected slot time to be present
- step 3: assertion_failure: expected slot customer_name to be present
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":404},"trace_id":"autonomous-eval-deterministic-20260422T172211Z-27ede721-booking_missing_name-4"}
- step 4: assertion_failure: expected status collecting, got response=None workflow=None
- step 4: assertion_failure: expected route workflow, got None
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 4: assertion_failure: reply missing expected text: telefone
- step 4: assertion_failure: expected action_result.missing_customer_phone=True, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
