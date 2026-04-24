# Chatbot Autonomous Tester Summary

- Iteration: 3
- Run ID: 20260420T133614Z-590a09db
- Mode: hybrid
- Started: 2026-04-20T13:36:14.487358+00:00
- Completed: 2026-04-20T13:37:25.536890+00:00
- Total scenarios: 26
- Pass: 12
- Fail: 14
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 6x ambiguous generated reschedule: Repeated date question
- 3x booking correction fragmented generated ptbr: Repeated date question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Top Failure Types

- 11x loop_detected
- 8x assertion_failure
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
- FAIL: generated_i0003_01_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0003_02_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0003_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0003_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0003_05_seed_missing_time_booking (2 findings)
- FAIL: generated_i0003_06_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0003_07_seed_reschedule_ambiguous (2 findings)
- PASS: generated_i0003_08_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0003_09_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0003_10_seed_missing_time_booking (2 findings)
- FAIL: generated_i0003_11_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0003_12_seed_reschedule_ambiguous (2 findings)
