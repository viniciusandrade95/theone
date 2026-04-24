# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-20T00:53:47.649321+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: e695f466-20e5-4b98-82a8-61d9ae834279
- Judge: disabled
- Total scenarios: 14
- Pass: 8
- Fail: 6
- Partial: 0

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 7x expected workflow reschedule_appointment, got None
- 7x unexpected RAG route
- 6x expected route workflow, got rag
- 4x expected slot new_date to be present
- 2x reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x expected action_result.ok=True, got False
- 2x expected status awaiting_confirmation, got response=ok workflow=None
- 2x expected slot new_time to be present
- 2x expected status collecting, got response=ok workflow=None
- 1x expected status completed, got response=ok workflow=None

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
