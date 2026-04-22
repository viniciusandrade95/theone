# Chatbot Autonomous Tester Summary

- Iteration: 5
- Run ID: 20260422T032748Z-d0a75b78
- Mode: hybrid
- Started: 2026-04-22T03:27:48.018383+00:00
- Completed: 2026-04-22T03:28:22.282391+00:00
- Total scenarios: 19
- Pass: 10
- Fail: 8
- Partial: 1
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking missing_phone guardrail: Repeated date question
- 1x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking fragmented state: Repeated date question

## Top Failure Types

- 3x evaluator.layer_mixing
- 3x conversation.slot_loop
- 3x conversation.state_reset
- 2x execution.crm_ambiguous_expected
- 2x conversation.short_confirmation_misrouted
- 2x conversation.time_flexible_mishandled
- 1x execution.crm_rejected

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
- PARTIAL: booking_with_colloquial_ptbr (1 findings)
- FAIL: reschedule_happy_path (3 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (3 findings)
- FAIL: generated_i0005_01_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0005_02_seed_missing_time_booking (2 findings)
- PASS: generated_i0005_03_seed_cancellation_colloquial (0 findings)
- FAIL: generated_i0005_04_seed_reschedule_ambiguous (1 findings)
- PASS: generated_i0005_05_seed_booking_with_faq_interruption (0 findings)
