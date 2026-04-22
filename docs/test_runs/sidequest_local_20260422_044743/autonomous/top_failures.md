# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T03:51:40.367367+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 30x booking fragmented state: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 30x booking fragmented state: expected route workflow, got None
- 30x booking fragmented state: expected workflow book_appointment, got None
- 25x booking missing_phone guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 25x booking missing_phone guardrail: expected route workflow, got None

## Most Frequent Bugs

- 835x conversation.state_reset
- 310x execution.runtime_internal_error
- 80x evaluator.wrong_expected_status
- 45x conversation.reference_disambiguation_failed
- 25x conversation.correction_mishandled
- 15x execution.identity_missing_block_expected
- 5x execution.crm_rejected
