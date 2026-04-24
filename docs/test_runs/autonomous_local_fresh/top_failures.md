# Autonomous Chatbot Top Failures

- Updated: 2026-04-19T22:21:38.868779+00:00
- Iterations tracked: 4

## Top 5 Failure Patterns

- 24x booking fragmented state: expected route workflow, got None
- 24x booking fragmented state: expected workflow book_appointment, got None
- 20x booking missing_phone guardrail: expected route workflow, got None
- 18x booking fragmented state: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 15x booking missing_phone guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I

## Most Frequent Bugs

- 788x assertion_failure
- 248x upstream_runtime_failure
- 12x failure_to_complete_task
- 4x crm_verification_failure
