# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T14:13:27.624652+00:00
- Iterations tracked: 6

## Top 5 Failure Patterns

- 32x ambiguous generated reschedule: Repeated time question
- 14x booking correction fragmented generated ptbr: Repeated date question
- 14x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 14x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 6x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 58x loop_detected
- 50x assertion_failure
- 14x failure_to_complete_task
- 6x crm_verification_failure
- 6x rag_during_operational_flow
