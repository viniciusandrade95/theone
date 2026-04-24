# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T16:09:38.296471+00:00
- Iterations tracked: 6

## Top 5 Failure Patterns

- 8x ambiguous generated reschedule: Repeated time question
- 6x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 6x booking happy_path crm_side_effect: expected matching appointment to exist
- 6x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 6x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed

## Most Frequent Bugs

- 45x assertion_failure
- 31x loop_detected
- 9x failure_to_complete_task
- 6x crm_verification_failure
- 6x rag_during_operational_flow
