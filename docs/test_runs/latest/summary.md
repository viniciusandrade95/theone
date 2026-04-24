# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-19T02:32:40.961780+00:00
- Base URL: https://theone-1-05gx.onrender.com
- Tenant ID: 4cd335f6-00bc-482a-8d91-154a775bcb7b
- Judge: disabled
- Total scenarios: 14
- Pass: 9
- Fail: 5
- Partial: 0

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 2x reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x expected workflow book_appointment, got create_lead
- 2x expected status awaiting_confirmation, got response=ok workflow=collecting
- 2x reply missing any expected text: remarcação, confirmar, confirmação
- 1x expected workflow book_appointment, got None
- 1x expected slot service to be present
- 1x expected slot date to be present
- 1x expected status completed, got response=ok workflow=awaiting_confirmation
- 1x expected workflow reschedule_appointment, got book_appointment
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
