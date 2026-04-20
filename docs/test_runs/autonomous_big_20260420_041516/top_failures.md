# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T03:21:35.120648+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 26x ambiguous generated reschedule: Repeated time question
- 24x ambiguous booking generated missing_time: Repeated time question
- 12x booking correction fragmented generated ptbr: Repeated time question
- 12x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 12x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got collecting

## Most Frequent Bugs

- 72x loop_detected
- 67x assertion_failure
- 12x failure_to_complete_task
- 5x rag_during_operational_flow
