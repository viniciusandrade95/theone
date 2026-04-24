# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T02:46:09.005994+00:00
- Iterations tracked: 3

## Top 5 Failure Patterns

- 6x ambiguous generated reschedule: Repeated time question
- 6x ambiguous booking generated missing_time: Repeated time question
- 3x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 3x booking happy_path crm_side_effect: expected matching appointment to exist
- 3x booking missing_phone guardrail: Repeated date question

## Most Frequent Bugs

- 36x assertion_failure
- 21x loop_detected
- 3x crm_verification_failure
- 3x rag_during_operational_flow
- 3x failure_to_complete_task
