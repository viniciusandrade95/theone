# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-20T01:08:20.307555+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 907ee7f1-d7f2-421f-a9c7-466ba8dd93b7
- Judge: disabled
- Total scenarios: 14
- Pass: 9
- Fail: 5
- Partial: 0

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 2x reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x expected action_result.ok=True, got False
- 2x expected status awaiting_confirmation, got response=ok workflow=collecting
- 2x reply missing any expected text: remarcação, confirmar, confirmação
- 1x expected status completed, got response=ok workflow=collecting
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- 1x reply missing any expected text: indisponível, disponibilidade, sugerir, remarcação, confirmar
- 1x expected workflow reschedule_appointment, got None
- 1x unexpected RAG route

## CRM Verification Failures

- 1x expected matching appointment to exist

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
