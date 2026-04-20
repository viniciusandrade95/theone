# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260420T053707Z-86b483d0
- Mode: hybrid
- Started: 2026-04-20T05:37:07.105314+00:00
- Completed: 2026-04-20T05:38:15.020767+00:00
- Total scenarios: 26
- Pass: 16
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking correction fragmented generated ptbr: Repeated date question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Repeated date question
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 13x assertion_failure
- 6x loop_detected
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
- PASS: generated_i0001_01_seed_reschedule_ambiguous (0 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (2 findings)
- PASS: generated_i0001_06_seed_reschedule_ambiguous (0 findings)
- PASS: generated_i0001_07_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_08_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_09_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_10_seed_missing_time_booking (2 findings)
- PASS: generated_i0001_11_seed_reschedule_ambiguous (0 findings)
- PASS: generated_i0001_12_seed_cancellation_colloquial (0 findings)
