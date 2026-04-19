# Autonomous Chatbot Top Failures

- Updated: 2026-04-19T03:06:15.220364+00:00
- Iterations tracked: 1

## Top 5 Failure Patterns

- 4x booking correction fragmented generated ptbr: Slot loss detected: date
- 3x booking missing_data guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 3x booking missing_data guardrail: expected route workflow, got None
- 3x booking missing_data guardrail: expected workflow book_appointment, got None
- 3x booking ptbr nlu colloquial: expected workflow book_appointment, got None

## Most Frequent Bugs

- 55x assertion_failure
- 8x upstream_runtime_failure
- 5x loop_detected
- 4x slot_loss
- 2x rag_during_operational_flow
- 2x failure_to_complete_task
- 1x crm_verification_failure
