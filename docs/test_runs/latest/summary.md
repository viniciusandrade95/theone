# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-18T15:22:09.916381+00:00
- Base URL: https://theone-1-05gx.onrender.com
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 10
- Pass: 4
- Fail: 6
- Partial: 0

## Upstream / Runtime Failures

- 3x HTTP request failed with status 0: 
- 3x response body is not a JSON object
- 1x HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"trace_id":"audit-eval-20260418T152209Z-5b0

## Product Logic Failures

- 4x expected route workflow, got None
- 4x expected workflow book_appointment, got None
- 4x reply missing expected text: confirmar
- 4x expected workflow book_appointment, got handoff_to_human
- 2x expected status awaiting_confirmation, got response=None workflow=None
- 2x expected slot service to be present
- 2x expected slot date to be present
- 2x expected slot time to be present
- 1x expected status completed, got response=None workflow=None
- 1x reply missing expected text: registr

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
