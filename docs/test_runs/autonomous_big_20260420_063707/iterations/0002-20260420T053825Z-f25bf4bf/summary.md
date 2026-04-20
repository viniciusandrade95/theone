# Chatbot Autonomous Tester Summary

- Iteration: 2
- Run ID: 20260420T053825Z-f25bf4bf
- Mode: hybrid
- Started: 2026-04-20T05:38:25.535502+00:00
- Completed: 2026-04-20T05:39:34.156273+00:00
- Total scenarios: 26
- Pass: 15
- Fail: 11
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 3x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 3x ambiguous booking generated missing_time: Repeated date question
- 2x booking correction fragmented generated ptbr: Repeated date question
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 14x assertion_failure
- 7x loop_detected
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
- PASS: generated_i0002_01_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0002_02_seed_missing_time_booking (2 findings)
- PASS: generated_i0002_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0002_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0002_05_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0002_06_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0002_07_seed_missing_time_booking (2 findings)
- PASS: generated_i0002_08_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0002_09_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0002_10_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0002_11_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0002_12_seed_missing_time_booking (2 findings)
