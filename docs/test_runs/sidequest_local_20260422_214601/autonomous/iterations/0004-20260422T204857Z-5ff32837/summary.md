# Chatbot Autonomous Tester Summary

- Iteration: 4
- Run ID: 20260422T204857Z-5ff32837
- Mode: hybrid
- Started: 2026-04-22T20:48:57.923186+00:00
- Completed: 2026-04-22T20:49:32.288172+00:00
- Total scenarios: 19
- Pass: 16
- Fail: 2
- Partial: 1
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: expected status completed, got response=ok workflow=awaiting_target_reference
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: Slot loss detected: time
- 1x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots

## Top Failure Types

- 2x execution.crm_ambiguous_expected
- 2x conversation.state_reset
- 1x execution.crm_rejected

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
- FAIL: reschedule_happy_path (3 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- PASS: reschedule_interrupted_then_resume (0 findings)
- PASS: generated_i0004_01_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0004_02_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0004_03_seed_colloquial_fragmented_booking (0 findings)
- PASS: generated_i0004_04_seed_reschedule_ambiguous (0 findings)
- FAIL: generated_i0004_05_seed_missing_time_booking (1 findings)
