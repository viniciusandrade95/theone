# Chatbot Hybrid Eval Summary

- Timestamp: 2026-04-22T20:54:04.463763+00:00
- Base URL: http://127.0.0.1:8000
- Tenant ID: 1bd1fced-8f18-4cc4-b7e5-b32b9401246a
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
