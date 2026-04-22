# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T20:46:12.494847+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: c0aa7c9e-cb43-40b2-9bd4-aefcb82c029b
- Judge: disabled
- Total scenarios: 14
- Pass: 12
- Fail: 1
- Partial: 1

## Upstream / Runtime Failures

- None

## Product Logic Failures

- 1x expected status completed, got response=ok workflow=awaiting_target_reference
- 1x reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## CRM Verification Failures

- 1x expected matching appointment to exist

## Failure Layers

- 3x execution

## Failure Families

- 2x execution.crm_ambiguous_expected
- 1x execution.crm_rejected

## Worst Conversational Scores

- Judge disabled or no scores

## Top Judge Issues

- None
