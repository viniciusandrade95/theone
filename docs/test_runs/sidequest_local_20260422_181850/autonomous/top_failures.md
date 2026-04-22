# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T17:23:24.698634+00:00
- Iterations tracked: 6

## Top 5 Failure Patterns

- 36x booking fragmented state: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","
- 36x booking fragmented state: expected route workflow, got None
- 36x booking fragmented state: expected workflow book_appointment, got None
- 30x booking missing_phone guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","
- 30x booking missing_phone guardrail: expected route workflow, got None

## Most Frequent Bugs

- 1002x conversation.state_reset
- 372x execution.runtime_internal_error
- 96x evaluator.wrong_expected_status
- 54x conversation.reference_disambiguation_failed
- 30x conversation.correction_mishandled
- 18x execution.identity_missing_block_expected
- 6x execution.crm_rejected
