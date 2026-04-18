# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-18T20:24:21.894224+00:00
- Base URL: https://theone-1-05gx.onrender.com
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 10
- Pass: 5
- Fail: 5
- Partial: 0

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 3x unexpected RAG route
- 3x expected workflow book_appointment, got None
- 2x reply missing expected text: confirmar
- 1x expected status completed, got response=ok workflow=collecting
- 1x reply missing expected text: registr
- 1x expected action_result.ok=True, got None
- 1x reply missing expected text: telefone
- 1x expected slot customer_name to be present
- 1x expected slot service to be present
- 1x expected slot date to be present

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
