# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T03:47:48.863502+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 82e54494-d4c0-4529-be81-6a3180b4cdca
- Judge: disabled
- Total scenarios: 14
- Pass: 0
- Fail: 14
- Partial: 0

## Upstream / Runtime Failures

- 40x HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"sidequest-20260422_044743-20260

## Product Logic Failures

- 31x expected workflow book_appointment, got None
- 29x expected route workflow, got None
- 18x expected slot service to be present
- 16x expected slot date to be present
- 15x expected slot time to be present
- 10x expected status awaiting_confirmation, got response=None workflow=None
- 8x expected status collecting, got response=None workflow=None
- 7x expected workflow reschedule_appointment, got None
- 5x reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 5x expected slot customer_name to be present

## CRM Verification Failures

- 1x expected matching appointment to exist

## Failure Layers

- 160x conversation
- 44x execution
- 13x evaluator

## Failure Families

- 134x conversation.state_reset
- 13x evaluator.wrong_expected_status
- 1x execution.crm_rejected
- 3x execution.identity_missing_block_expected
- 40x execution.runtime_internal_error

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
