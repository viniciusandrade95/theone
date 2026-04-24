# Chatbot Autonomous Tester Summary

- Iteration: 3
- Run ID: 20260420T160547Z-1007ed6d
- Mode: hybrid
- Started: 2026-04-20T16:05:47.678311+00:00
- Completed: 2026-04-20T16:06:38.189957+00:00
- Total scenarios: 22
- Pass: 11
- Fail: 11
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking correction fragmented generated ptbr: Repeated date question
- 2x ambiguous generated reschedule: Repeated time question
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking missing_phone guardrail: Repeated date question

## Top Failure Types

- 7x assertion_failure
- 6x loop_detected
- 1x crm_verification_failure
- 1x rag_during_operational_flow
- 1x failure_to_complete_task

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
- FAIL: generated_i0003_02_seed_reschedule_ambiguous (1 findings)
- PASS: generated_i0003_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0003_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0003_05_seed_missing_time_booking (2 findings)
- FAIL: generated_i0003_06_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0003_07_seed_reschedule_ambiguous (1 findings)
- PASS: generated_i0003_08_seed_cancellation_colloquial (0 findings)
