# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T143403Z-50d50d45
- Mode: hybrid
- Started: 2026-04-19T14:34:03.532307+00:00
- Completed: 2026-04-19T14:44:09.181905+00:00
- Total scenarios: 19
- Pass: 11
- Fail: 8
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking affirmation short_turns: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 2x booking affirmation short_turns: expected workflow book_appointment, got None
- 2x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 2x ambiguous generated reschedule: unexpected RAG route
- 2x ambiguous generated reschedule: expected workflow reschedule_appointment, got book_appointment

## Top Failure Types

- 25x assertion_failure
- 3x loop_detected
- 3x rag_during_operational_flow
- 2x upstream_runtime_failure
- 1x crm_verification_failure
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- PASS: booking_missing_name (0 findings)
- PASS: booking_missing_phone (0 findings)
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
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (7 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (6 findings)
