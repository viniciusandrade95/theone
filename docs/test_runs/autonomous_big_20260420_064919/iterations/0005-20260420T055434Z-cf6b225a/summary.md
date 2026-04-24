# Chatbot Autonomous Tester Summary

- Iteration: 5
- Run ID: 20260420T055434Z-cf6b225a
- Mode: hybrid
- Started: 2026-04-20T05:54:34.293296+00:00
- Completed: 2026-04-20T05:55:43.821435+00:00
- Total scenarios: 26
- Pass: 14
- Fail: 12
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 4x ambiguous generated reschedule: Repeated date question
- 3x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 3x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 15x assertion_failure
- 7x loop_detected
- 3x failure_to_complete_task
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
- FAIL: booking_with_colloquial_ptbr (2 findings)
- FAIL: reschedule_happy_path (4 findings)
- FAIL: reschedule_conflict (1 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- PASS: generated_i0005_01_seed_colloquial_fragmented_booking (0 findings)
- FAIL: generated_i0005_02_seed_missing_time_booking (2 findings)
- PASS: generated_i0005_03_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0005_04_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0005_05_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0005_06_seed_colloquial_fragmented_booking (0 findings)
- FAIL: generated_i0005_07_seed_missing_time_booking (2 findings)
- PASS: generated_i0005_08_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0005_09_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0005_10_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0005_11_seed_colloquial_fragmented_booking (0 findings)
- FAIL: generated_i0005_12_seed_missing_time_booking (2 findings)
