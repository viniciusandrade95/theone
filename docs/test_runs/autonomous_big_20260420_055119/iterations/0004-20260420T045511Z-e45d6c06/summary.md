# Chatbot Autonomous Tester Summary

- Iteration: 4
- Run ID: 20260420T045511Z-e45d6c06
- Mode: hybrid
- Started: 2026-04-20T04:55:11.556119+00:00
- Completed: 2026-04-20T04:56:18.761315+00:00
- Total scenarios: 26
- Pass: 16
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking correction fragmented generated ptbr: Repeated time question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 13x assertion_failure
- 4x loop_detected
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
- PASS: generated_i0004_01_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_02_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0004_03_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0004_04_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0004_05_seed_missing_time_booking (2 findings)
- PASS: generated_i0004_06_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_07_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0004_08_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0004_09_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0004_10_seed_missing_time_booking (2 findings)
- PASS: generated_i0004_11_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_12_seed_booking_with_faq_interruption (0 findings)
