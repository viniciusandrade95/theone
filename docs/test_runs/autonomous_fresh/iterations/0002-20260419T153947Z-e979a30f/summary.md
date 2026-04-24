# Chatbot Autonomous Tester Summary

- Iteration: 2
- Run ID: 20260419T153947Z-e979a30f
- Mode: hybrid
- Started: 2026-04-19T15:39:47.723863+00:00
- Completed: 2026-04-19T15:49:12.520489+00:00
- Total scenarios: 19
- Pass: 12
- Fail: 7
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: expected status awaiting_confirmation, got response=ok workflow=collecting
- 1x reschedule happy_path crm_side_effect requires_existing_appointment: reply missing any expected text: remarcação, confirmar, confirmação

## Top Failure Types

- 17x assertion_failure
- 3x rag_during_operational_flow
- 3x loop_detected
- 1x crm_verification_failure
- 1x upstream_runtime_failure
- 1x failure_to_complete_task

## Scenario Verdicts

- FAIL: booking_happy_path_full (2 findings)
- PASS: booking_missing_name (0 findings)
- PASS: booking_missing_phone (0 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- FAIL: booking_with_fragmented_inputs (1 findings)
- PASS: booking_with_colloquial_ptbr (0 findings)
- FAIL: reschedule_happy_path (8 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0002_01_seed_reschedule_ambiguous (4 findings)
- FAIL: generated_i0002_02_seed_missing_time_booking (5 findings)
- PASS: generated_i0002_03_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0002_04_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0002_05_seed_colloquial_fragmented_booking (1 findings)
