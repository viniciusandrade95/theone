# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T031011Z-e2c01790
- Mode: hybrid
- Started: 2026-04-19T03:10:11.544725+00:00
- Completed: 2026-04-19T03:19:01.829534+00:00
- Total scenarios: 19
- Pass: 9
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 3x booking ptbr nlu colloquial: expected workflow book_appointment, got None
- 2x booking ptbr nlu colloquial: unexpected RAG route
- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking missing_phone guardrail: Repeated date question
- 1x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Top Failure Types

- 25x assertion_failure
- 5x loop_detected
- 3x rag_during_operational_flow
- 1x upstream_runtime_failure
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (1 findings)
- PASS: booking_missing_name (0 findings)
- FAIL: booking_missing_phone (1 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- FAIL: booking_with_fragmented_inputs (2 findings)
- FAIL: booking_with_colloquial_ptbr (8 findings)
- FAIL: reschedule_happy_path (5 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (4 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0001_03_seed_booking_with_faq_interruption (2 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (6 findings)
