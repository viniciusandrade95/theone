# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T04:57:37.053065+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 12x booking correction fragmented generated ptbr: Repeated time question
- 12x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 12x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 5x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 5x booking happy_path crm_side_effect: expected matching appointment to exist

## Most Frequent Bugs

- 67x assertion_failure
- 22x loop_detected
- 12x failure_to_complete_task
- 5x crm_verification_failure
- 5x rag_during_operational_flow
