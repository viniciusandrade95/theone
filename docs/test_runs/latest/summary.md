# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-18T14:11:40.124646+00:00
- Base URL: https://theone-1-05gx.onrender.com
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 10
- Pass: 0
- Fail: 10
- Partial: 0

## Common Failure Patterns

- 29x HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","status":502},"trace_id":"audit-eval-2026
- 27x expected workflow book_appointment, got None
- 14x expected route workflow, got None
- 14x expected slot service to be present
- 12x expected slot date to be present
- 11x expected slot time to be present
- 4x reply missing expected text: confirmar
- 3x expected status awaiting_confirmation, got response=None workflow=None
- 2x reply missing expected text: telefone
- 1x expected status completed, got response=None workflow=None

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
