# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T03:53:45.746180+00:00
- Iterations tracked: 7

## Top 5 Failure Patterns

- 36x ambiguous generated reschedule: Repeated time question
- 32x ambiguous booking generated missing_time: Repeated time question
- 17x booking correction fragmented generated ptbr: Repeated time question
- 16x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 16x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got collecting

## Most Frequent Bugs

- 99x loop_detected
- 93x assertion_failure
- 16x failure_to_complete_task
- 7x crm_verification_failure
- 7x rag_during_operational_flow
