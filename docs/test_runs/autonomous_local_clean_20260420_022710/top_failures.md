# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T01:29:29.850154+00:00
- Iterations tracked: 2

## Top 5 Failure Patterns

- 2x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 2x booking happy_path crm_side_effect: expected action_result.ok=True, got False
- 2x booking happy_path crm_side_effect: expected matching appointment to exist
- 2x booking missing_phone guardrail: Repeated date question
- 2x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 28x assertion_failure
- 6x loop_detected
- 2x crm_verification_failure
- 2x rag_during_operational_flow
- 2x failure_to_complete_task
