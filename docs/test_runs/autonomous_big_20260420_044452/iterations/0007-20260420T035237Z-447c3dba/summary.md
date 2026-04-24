# Chatbot Autonomous Tester Summary

- Iteration: 7
- Run ID: 20260420T035237Z-447c3dba
- Mode: hybrid
- Started: 2026-04-20T03:52:37.569849+00:00
- Completed: 2026-04-20T03:53:45.745042+00:00
- Total scenarios: 26
- Pass: 13
- Fail: 13
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 4x ambiguous booking generated missing_time: Repeated time question
- 4x ambiguous generated reschedule: Repeated time question
- 3x booking correction fragmented generated ptbr: Repeated time question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got collecting

## Top Failure Types

- 13x assertion_failure
- 13x loop_detected
- 2x failure_to_complete_task
- 1x crm_verification_failure
- 1x rag_during_operational_flow

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- PASS: booking_missing_name (0 findings)
- FAIL: booking_missing_phone (1 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- FAIL: booking_with_fragmented_inputs (2 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (4 findings)
- FAIL: reschedule_conflict (1 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- PASS: generated_i0007_01_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0007_02_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0007_03_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0007_04_seed_missing_time_booking (4 findings)
- FAIL: generated_i0007_05_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0007_06_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0007_07_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0007_08_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0007_09_seed_missing_time_booking (4 findings)
- FAIL: generated_i0007_10_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0007_11_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0007_12_seed_colloquial_fragmented_booking (1 findings)
