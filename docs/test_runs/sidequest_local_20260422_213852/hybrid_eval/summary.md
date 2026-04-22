# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T20:39:03.261225+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 647eca36-2f81-4850-b396-555228f56f4b
- Judge: disabled
- Total scenarios: 14
- Pass: 11
- Fail: 1
- Partial: 2

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 1x reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 1x expected status completed, got response=ok workflow=awaiting_target_reference
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## CRM Verification Failures

- 1x expected matching appointment to exist

## Failure Layers

- 3x execution
- 1x evaluator

## Failure Families

- 1x evaluator.layer_mixing
- 2x execution.crm_ambiguous_expected
- 1x execution.crm_rejected

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
