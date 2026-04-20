# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T13:40:03.706995+00:00
- Iterations tracked: 11

## Top 5 Failure Patterns

- 58x ambiguous generated reschedule: Repeated date question
- 26x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 26x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 12x booking correction fragmented generated ptbr: Repeated date question
- 11x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 128x assertion_failure
- 98x loop_detected
- 26x failure_to_complete_task
- 11x crm_verification_failure
- 11x rag_during_operational_flow
