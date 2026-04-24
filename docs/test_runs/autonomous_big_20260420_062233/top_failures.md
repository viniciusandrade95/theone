# Autonomous Chatbot Top Failures

- Updated: 2026-04-20T05:24:51.170247+00:00
- Iterations tracked: 2

## Top 5 Failure Patterns

- 24x ambiguous generated reschedule: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 24x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 20x booking faq generated interruption: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 15x ambiguous booking generated missing_time: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 15x ambiguous booking generated missing_time: expected workflow book_appointment, got None

## Most Frequent Bugs

- 452x assertion_failure
- 184x upstream_runtime_failure
- 13x failure_to_complete_task
- 2x crm_verification_failure
