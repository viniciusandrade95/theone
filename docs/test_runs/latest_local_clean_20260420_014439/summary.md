# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-20T00:44:39.144513+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: e695f466-20e5-4b98-82a8-61d9ae834279
- Judge: disabled
- Total scenarios: 14
- Pass: 0
- Fail: 14
- Partial: 0

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 20x unexpected RAG route
- 17x expected route workflow, got rag
- 13x expected workflow book_appointment, got None
- 11x expected slot service to be present
- 7x expected workflow reschedule_appointment, got None
- 5x reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 5x expected status awaiting_confirmation, got response=ok workflow=None
- 5x expected slot date to be present
- 5x expected slot time to be present
- 5x expected status collecting, got response=ok workflow=None

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
