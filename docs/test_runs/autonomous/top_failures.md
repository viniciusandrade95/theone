# Autonomous Chatbot Top Failures

- Updated: 2026-04-19T14:55:00.432975+00:00
- Iterations tracked: 8

## Top 5 Failure Patterns

- 18x booking fragmented state: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name
- 18x booking fragmented state: response body is not a JSON object
- 18x booking fragmented state: expected route workflow, got None
- 18x booking fragmented state: expected workflow book_appointment, got None
- 15x booking missing_phone guardrail: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name

## Most Frequent Bugs

- 759x assertion_failure
- 357x upstream_runtime_failure
- 21x loop_detected
- 15x rag_during_operational_flow
- 13x failure_to_complete_task
- 7x crm_verification_failure
- 6x slot_loss
