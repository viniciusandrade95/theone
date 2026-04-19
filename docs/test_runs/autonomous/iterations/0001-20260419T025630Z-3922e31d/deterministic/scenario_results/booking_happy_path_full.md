# booking_happy_path_full

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888
Turn 1 assistant: 
Turn 2 user: sim, pode confirmar
Turn 2 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 0: 
- step 1: upstream_runtime_failure: response body is not a JSON object
- step 1: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 1: assertion_failure: expected slot customer_name to be present
- step 1: assertion_failure: expected slot phone to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 0: 
- step 2: upstream_runtime_failure: response body is not a JSON object
- step 2: assertion_failure: expected status completed, got response=None workflow=None
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 2: assertion_failure: expected action_result.ok=True, got None
- crm_verification_failure: CRM appointments query failed with status 0

## CRM Verification

```json
{
  "status_code": 0,
  "raw_body": "",
  "parsed_body": null,
  "reasons": [
    "CRM appointments query failed with status 0"
  ],
  "status": "FAIL"
}
```
