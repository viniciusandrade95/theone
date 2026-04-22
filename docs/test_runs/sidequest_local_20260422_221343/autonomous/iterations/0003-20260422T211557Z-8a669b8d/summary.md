# Chatbot Autonomous Tester Summary

- Iteration: 3
- Run ID: 20260422T211557Z-8a669b8d
- Mode: hybrid
- Started: 2026-04-22T21:15:57.545494+00:00
- Completed: 2026-04-22T21:16:33.816337+00:00
- Total scenarios: 19
- Pass: 17
- Fail: 1
- Partial: 1
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## Top Failure Types

- 2x execution.crm_rejected

## Scenario Verdicts

- PARTIAL: booking_happy_path_full (1 findings)
- PASS: booking_missing_name (0 findings)
- PASS: booking_missing_phone (0 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- PASS: booking_with_fragmented_inputs (0 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (1 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- PASS: reschedule_interrupted_then_resume (0 findings)
- PASS: generated_i0003_01_seed_colloquial_fragmented_booking (0 findings)
- PASS: generated_i0003_02_seed_reschedule_ambiguous (0 findings)
- PASS: generated_i0003_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0003_04_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0003_05_seed_missing_time_booking (0 findings)
