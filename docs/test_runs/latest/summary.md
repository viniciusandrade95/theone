# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-18T15:57:18.211936+00:00
- Base URL: https://theone-1-05gx.onrender.com
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 10
- Pass: 3
- Fail: 7
- Partial: 0

## Upstream / Runtime Failures

- 2x HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"audit-eval-20260418T155718Z-d11
- 1x HTTP request failed with status 0: 
- 1x response body is not a JSON object

## Product Logic Failures

- 4x reply missing expected text: confirmar
- 4x expected workflow book_appointment, got handoff_to_human
- 3x expected workflow book_appointment, got None
- 2x expected route workflow, got None
- 2x expected slot service to be present
- 2x expected slot date to be present
- 2x expected slot time to be present
- 1x expected status awaiting_confirmation, got response=None workflow=None
- 1x expected status completed, got response=None workflow=None
- 1x reply missing expected text: registr

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
