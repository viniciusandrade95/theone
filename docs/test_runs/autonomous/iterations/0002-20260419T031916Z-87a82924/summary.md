# Chatbot Autonomous Tester Summary

- Iteration: 2
- Run ID: 20260419T031916Z-87a82924
- Mode: hybrid
- Started: 2026-04-19T03:19:16.835467+00:00
- Completed: 2026-04-19T03:28:26.800804+00:00
- Total scenarios: 19
- Pass: 9
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 2x booking ptbr nlu colloquial: expected workflow book_appointment, got create_lead
- 2x booking correction fragmented generated ptbr: expected workflow book_appointment, got None
- 2x booking correction fragmented generated ptbr: Slot loss detected: date
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist

## Top Failure Types

- 25x assertion_failure
- 4x loop_detected
- 4x rag_during_operational_flow
- 2x failure_to_complete_task
- 2x upstream_runtime_failure
- 2x slot_loss
- 1x crm_verification_failure

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
- FAIL: booking_with_colloquial_ptbr (5 findings)
- FAIL: reschedule_happy_path (5 findings)
- FAIL: reschedule_conflict (1 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0002_01_seed_reschedule_ambiguous (4 findings)
- FAIL: generated_i0002_02_seed_missing_time_booking (6 findings)
- PASS: generated_i0002_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0002_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0002_05_seed_colloquial_fragmented_booking (9 findings)
