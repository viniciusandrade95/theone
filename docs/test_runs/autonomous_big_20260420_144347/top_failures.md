# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T13:47:31.213110+00:00
- Iterations tracked: 3

## Top 5 Failure Patterns

- 18x ambiguous generated reschedule: Repeated date question
- 7x booking correction fragmented generated ptbr: Repeated date question
- 7x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 7x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 3x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 31x loop_detected
- 25x assertion_failure
- 7x failure_to_complete_task
- 3x crm_verification_failure
- 3x rag_during_operational_flow
