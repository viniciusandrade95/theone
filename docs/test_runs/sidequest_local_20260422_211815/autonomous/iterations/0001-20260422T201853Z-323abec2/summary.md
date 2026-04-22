# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260422T201853Z-323abec2
- Mode: hybrid
- Started: 2026-04-22T20:18:53.444096+00:00
- Completed: 2026-04-22T20:19:28.566467+00:00
- Total scenarios: 19
- Pass: 9
- Fail: 9
- Partial: 1
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking missing_data guardrail: expected status awaiting_confirmation, got response=ok workflow=collecting
- 1x booking missing_phone guardrail: expected status awaiting_confirmation, got response=ok workflow=collecting
- 1x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Top Failure Types

- 3x evaluator.layer_mixing
- 3x conversation.state_reset
- 2x execution.identity_missing_block_expected
- 2x conversation.slot_loop
- 2x execution.crm_ambiguous_expected
- 2x conversation.short_confirmation_misrouted
- 2x conversation.time_flexible_mishandled
- 1x execution.crm_rejected

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- FAIL: booking_missing_name (1 findings)
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
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (1 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (1 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (2 findings)
