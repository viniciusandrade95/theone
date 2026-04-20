# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T05:39:34.157009+00:00
- Iterations tracked: 2

## Top 5 Failure Patterns

- 5x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 5x ambiguous booking generated missing_time: Repeated date question
- 4x booking correction fragmented generated ptbr: Repeated date question
- 2x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x booking happy_path crm_side_effect: expected matching appointment to exist

## Most Frequent Bugs

- 27x assertion_failure
- 13x loop_detected
- 2x crm_verification_failure
- 2x rag_during_operational_flow
