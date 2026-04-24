# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T05:29:39.403039+00:00
- Iterations tracked: 8

## Top 5 Failure Patterns

- 19x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 19x ambiguous booking generated missing_time: Repeated date question
- 12x booking correction fragmented generated ptbr: Repeated time question
- 8x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 8x booking happy_path crm_side_effect: expected matching appointment to exist

## Most Frequent Bugs

- 107x assertion_failure
- 54x loop_detected
- 8x crm_verification_failure
- 8x rag_during_operational_flow
