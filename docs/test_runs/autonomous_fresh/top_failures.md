# Autonomous Chatbot Top Failures

- Updated: 2026-04-19T16:48:07.828440+00:00
- Iterations tracked: 4

## Top 5 Failure Patterns

- 4x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 4x booking happy_path crm_side_effect: expected matching appointment to exist
- 2x booking affirmation short_turns: expected workflow book_appointment, got None
- 2x booking affirmation short_turns: unexpected RAG route
- 2x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 78x assertion_failure
- 16x loop_detected
- 8x upstream_runtime_failure
- 7x rag_during_operational_flow
- 4x crm_verification_failure
- 4x failure_to_complete_task
