# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: 
Turn 2 user: Corte
Turn 2 assistant: 
Turn 3 user: amanhã
Turn 3 assistant: 
Turn 4 user: 16h17
Turn 4 assistant: 
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: 
Turn 6 user: sim, pode confirmar
Turn 6 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 1: assertion_failure: expected status collecting, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: reply missing expected text: serviço
- step 2: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 2: assertion_failure: expected status collecting, got response=None workflow=None
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: expected slot service to be present
- step 3: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 3: assertion_failure: expected status collecting, got response=None workflow=None
- step 3: assertion_failure: expected route workflow, got None
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 4: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 4: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 4: assertion_failure: expected route workflow, got None
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 4: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 4: assertion_failure: expected slot service to be present
- step 4: assertion_failure: expected slot date to be present
- step 4: assertion_failure: expected slot time to be present
- step 5: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 5: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 5: assertion_failure: expected route workflow, got None
- step 5: assertion_failure: expected workflow book_appointment, got None
- step 5: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 5: assertion_failure: expected slot service to be present
- step 5: assertion_failure: expected slot date to be present
- step 5: assertion_failure: expected slot time to be present
- step 5: assertion_failure: expected slot customer_name to be present
- step 5: assertion_failure: expected slot phone to be present
- step 6: upstream_runtime_failure: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-ID"}}
- step 6: assertion_failure: expected status completed, got response=None workflow=None
- step 6: assertion_failure: expected route workflow, got None
- step 6: assertion_failure: expected workflow book_appointment, got None
- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 6: assertion_failure: expected action_result.ok=True, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
