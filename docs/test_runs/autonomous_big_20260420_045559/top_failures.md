# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T04:01:00.410821+00:00
- Iterations tracked: 4

## Top 5 Failure Patterns

- 22x ambiguous generated reschedule: Repeated time question
- 18x ambiguous booking generated missing_time: Repeated time question
- 9x booking correction fragmented generated ptbr: Repeated time question
- 9x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 9x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got collecting

## Most Frequent Bugs

- 57x loop_detected
- 53x assertion_failure
- 9x failure_to_complete_task
- 4x crm_verification_failure
- 4x rag_during_operational_flow
