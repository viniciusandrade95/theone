# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T20:18:23.408144+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: e2d2743a-4fce-45e7-af58-1b67e15d4fce
- Judge: disabled
- Total scenarios: 14
- Pass: 7
- Fail: 5
- Partial: 2

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 2x reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x expected status awaiting_confirmation, got response=ok workflow=collecting
- 1x reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 1x expected status completed, got response=ok workflow=awaiting_target_reference
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- 1x expected workflow reschedule_appointment, got None
- 1x unexpected RAG route

## CRM Verification Failures

- 1x expected matching appointment to exist

## Failure Layers

- 5x execution
- 3x evaluator
- 2x conversation

## Failure Families

- 1x conversation.short_confirmation_misrouted
- 1x conversation.state_reset
- 3x evaluator.layer_mixing
- 2x execution.crm_ambiguous_expected
- 1x execution.crm_rejected
- 2x execution.identity_missing_block_expected

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
