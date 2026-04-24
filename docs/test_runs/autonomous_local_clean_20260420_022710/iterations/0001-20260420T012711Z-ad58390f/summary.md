# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260420T012711Z-ad58390f
- Mode: hybrid
- Started: 2026-04-20T01:27:11.093330+00:00
- Completed: 2026-04-20T01:28:12.360803+00:00
- Total scenarios: 19
- Pass: 12
- Fail: 7
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 1x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 1x booking happy_path crm_side_effect: expected action_result.ok=True, got False
- 1x booking happy_path crm_side_effect: expected matching appointment to exist
- 1x booking missing_phone guardrail: Repeated date question
- 1x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Top Failure Types

- 14x assertion_failure
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
- PASS: generated_i0001_01_seed_reschedule_ambiguous (0 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- PASS: generated_i0001_04_seed_colloquial_fragmented_booking (0 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (3 findings)
