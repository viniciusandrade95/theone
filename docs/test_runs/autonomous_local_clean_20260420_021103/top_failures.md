# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T01:15:53.973742+00:00
- Iterations tracked: 4

## Top 5 Failure Patterns

- 8x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 8x ambiguous generated reschedule: unexpected RAG route
- 8x ambiguous generated reschedule: expected workflow reschedule_appointment, got book_appointment
- 4x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 4x booking happy_path crm_side_effect: expected action_result.ok=True, got False

## Most Frequent Bugs

- 80x assertion_failure
- 12x loop_detected
- 4x crm_verification_failure
- 4x rag_during_operational_flow
- 4x failure_to_complete_task
