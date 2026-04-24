# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T04:36:43.424339+00:00
- Iterations tracked: 2

## Top 5 Failure Patterns

- 12x ambiguous generated reschedule: Repeated time question
- 5x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 5x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 4x booking correction fragmented generated ptbr: Repeated time question
- 2x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 27x assertion_failure
- 20x loop_detected
- 5x failure_to_complete_task
- 2x crm_verification_failure
- 2x rag_during_operational_flow
