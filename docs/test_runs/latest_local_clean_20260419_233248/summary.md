# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-19T22:32:49.043920+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 14
- Pass: 0
- Fail: 14
- Partial: 0

## Upstream / Runtime Failures

- 40x HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}

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

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
