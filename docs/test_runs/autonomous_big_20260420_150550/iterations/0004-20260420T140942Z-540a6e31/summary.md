# Chatbot Autonomous Tester Summary

- Iteration: 4
- Run ID: 20260420T140942Z-540a6e31
- Mode: hybrid
- Started: 2026-04-20T14:09:42.849222+00:00
- Completed: 2026-04-20T14:10:51.168301+00:00
- Total scenarios: 26
- Pass: 14
- Fail: 12
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 4x ambiguous generated reschedule: Repeated time question
- 2x booking correction fragmented generated ptbr: Repeated date question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Top Failure Types

- 8x assertion_failure
- 8x loop_detected
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
- FAIL: booking_with_colloquial_ptbr (1 findings)
- FAIL: reschedule_happy_path (1 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (3 findings)
- PASS: generated_i0004_01_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_02_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0004_03_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0004_04_seed_reschedule_ambiguous (2 findings)
- FAIL: generated_i0004_05_seed_missing_time_booking (2 findings)
- PASS: generated_i0004_06_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_07_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0004_08_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0004_09_seed_reschedule_ambiguous (2 findings)
- FAIL: generated_i0004_10_seed_missing_time_booking (2 findings)
- PASS: generated_i0004_11_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_12_seed_booking_with_faq_interruption (0 findings)
