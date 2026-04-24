# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T04:40:57.962255+00:00
- Iterations tracked: 1

## Top 5 Failure Patterns

- 6x ambiguous generated reschedule: Repeated time question
- 2x booking correction fragmented generated ptbr: Repeated time question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 13x assertion_failure
- 10x loop_detected
- 2x failure_to_complete_task
- 1x crm_verification_failure
- 1x rag_during_operational_flow
