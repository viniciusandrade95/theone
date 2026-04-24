# Chatbot Autonomous Tester Summary

- Iteration: 6
- Run ID: 20260420T160848Z-9a4dedd2
- Mode: hybrid
- Started: 2026-04-20T16:08:48.972709+00:00
- Completed: 2026-04-20T16:09:38.295487+00:00
- Total scenarios: 22
- Pass: 11
- Fail: 11
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x ambiguous generated reschedule: Repeated time question
- 2x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots
- 2x ambiguous booking generated missing_time: Expected final status awaiting_confirmation, got completed
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 8x assertion_failure
- 5x loop_detected
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
- PASS: generated_i0006_01_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0006_02_seed_reschedule_ambiguous (1 findings)
- FAIL: generated_i0006_03_seed_missing_time_booking (2 findings)
- FAIL: generated_i0006_04_seed_colloquial_fragmented_booking (1 findings)
- PASS: generated_i0006_05_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0006_06_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0006_07_seed_reschedule_ambiguous (1 findings)
- FAIL: generated_i0006_08_seed_missing_time_booking (2 findings)
