# Chatbot Autonomous Tester Summary

- Iteration: 3
- Run ID: 20260420T011336Z-f0347a0e
- Mode: hybrid
- Started: 2026-04-20T01:13:36.259024+00:00
- Completed: 2026-04-20T01:14:37.661017+00:00
- Total scenarios: 19
- Pass: 11
- Fail: 8
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 2x ambiguous generated reschedule: unexpected RAG route
- 2x ambiguous generated reschedule: expected workflow reschedule_appointment, got book_appointment
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected action_result.ok=True, got False

## Top Failure Types

- 20x assertion_failure
- 3x loop_detected
- 1x crm_verification_failure
- 1x rag_during_operational_flow
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (3 findings)
- PASS: booking_missing_name (0 findings)
- FAIL: booking_missing_phone (1 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- FAIL: booking_with_fragmented_inputs (3 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (4 findings)
- FAIL: reschedule_conflict (1 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- PASS: generated_i0003_01_seed_colloquial_fragmented_booking (0 findings)
- FAIL: generated_i0003_02_seed_reschedule_ambiguous (6 findings)
- PASS: generated_i0003_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0003_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0003_05_seed_missing_time_booking (3 findings)
