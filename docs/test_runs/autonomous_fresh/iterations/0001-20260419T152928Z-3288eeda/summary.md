# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T152928Z-3288eeda
- Mode: hybrid
- Started: 2026-04-19T15:29:28.538896+00:00
- Completed: 2026-04-19T15:39:32.713091+00:00
- Total scenarios: 19
- Pass: 10
- Fail: 9
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking affirmation short_turns: expected workflow book_appointment, got None
- 2x booking affirmation short_turns: unexpected RAG route
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking affirmation short_turns: expected slot service to be present

## Top Failure Types

- 33x assertion_failure
- 3x upstream_runtime_failure
- 3x loop_detected
- 2x rag_during_operational_flow
- 1x crm_verification_failure
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- PASS: booking_missing_name (0 findings)
- PASS: booking_missing_phone (0 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- FAIL: booking_with_short_affirmations (7 findings)
- FAIL: booking_with_fragmented_inputs (11 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (7 findings)
- FAIL: reschedule_conflict (1 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (3 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (6 findings)
