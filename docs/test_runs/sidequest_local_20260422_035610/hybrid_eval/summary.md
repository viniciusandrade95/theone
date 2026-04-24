# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T02:56:11.265217+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 82e54494-d4c0-4529-be81-6a3180b4cdca
- Judge: disabled
- Total scenarios: 14
- Pass: 9
- Fail: 3
- Partial: 2

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 2x reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 1x expected status completed, got response=ok workflow=awaiting_target_reference
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- 1x expected workflow reschedule_appointment, got None
- 1x unexpected RAG route

## CRM Verification Failures

- 1x expected matching appointment to exist

## Failure Layers

- 3x evaluator
- 3x execution
- 2x conversation

## Failure Families

- 1x conversation.short_confirmation_misrouted
- 1x conversation.state_reset
- 3x evaluator.layer_mixing
- 2x execution.crm_ambiguous_expected
- 1x execution.crm_rejected

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
