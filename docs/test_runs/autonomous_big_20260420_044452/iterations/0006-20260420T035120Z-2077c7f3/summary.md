# Chatbot Autonomous Tester Summary

- Iteration: 6
- Run ID: 20260420T035120Z-2077c7f3
- Mode: hybrid
- Started: 2026-04-20T03:51:20.716899+00:00
- Completed: 2026-04-20T03:52:27.566181+00:00
- Total scenarios: 26
- Pass: 13
- Fail: 13
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 6x ambiguous generated reschedule: Repeated time question
- 4x ambiguous booking generated missing_time: Repeated time question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got collecting
- 2x booking correction fragmented generated ptbr: Repeated time question

## Top Failure Types

- 14x loop_detected
- 13x assertion_failure
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
- PASS: generated_i0006_01_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0006_02_seed_reschedule_ambiguous (2 findings)
- FAIL: generated_i0006_03_seed_missing_time_booking (4 findings)
- FAIL: generated_i0006_04_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0006_05_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0006_06_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0006_07_seed_reschedule_ambiguous (2 findings)
- FAIL: generated_i0006_08_seed_missing_time_booking (4 findings)
- FAIL: generated_i0006_09_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0006_10_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0006_11_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0006_12_seed_reschedule_ambiguous (2 findings)
