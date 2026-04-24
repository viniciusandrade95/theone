# Chatbot Autonomous Tester Summary

- Iteration: 2
- Run ID: 20260419T144424Z-141fe370
- Mode: hybrid
- Started: 2026-04-19T14:44:24.191598+00:00
- Completed: 2026-04-19T14:55:00.429998+00:00
- Total scenarios: 19
- Pass: 9
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 4x booking missing_data guardrail: expected workflow book_appointment, got None
- 3x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 3x ambiguous generated reschedule: unexpected RAG route
- 2x booking missing_data guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 2x booking missing_data guardrail: expected route workflow, got None

## Top Failure Types

- 52x assertion_failure
- 4x loop_detected
- 3x rag_during_operational_flow
- 2x upstream_runtime_failure
- 1x crm_verification_failure
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- FAIL: booking_missing_name (26 findings)
- FAIL: booking_missing_phone (1 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- FAIL: booking_with_short_affirmations (7 findings)
- FAIL: booking_with_fragmented_inputs (2 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (5 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0002_01_seed_reschedule_ambiguous (8 findings)
- FAIL: generated_i0002_02_seed_missing_time_booking (6 findings)
- PASS: generated_i0002_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0002_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0002_05_seed_colloquial_fragmented_booking (1 findings)
