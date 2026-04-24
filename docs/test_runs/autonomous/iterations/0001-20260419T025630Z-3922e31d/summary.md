# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T025630Z-3922e31d
- Mode: hybrid
- Started: 2026-04-19T02:56:30.022454+00:00
- Completed: 2026-04-19T03:06:15.217483+00:00
- Total scenarios: 19
- Pass: 9
- Fail: 10
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 4x booking correction fragmented generated ptbr: Slot loss detected: date
- 3x booking missing_data guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service unavailable"},"tr
- 3x booking missing_data guardrail: expected route workflow, got None
- 3x booking missing_data guardrail: expected workflow book_appointment, got None
- 3x booking ptbr nlu colloquial: expected workflow book_appointment, got None

## Top Failure Types

- 55x assertion_failure
- 8x upstream_runtime_failure
- 5x loop_detected
- 4x slot_loss
- 2x rag_during_operational_flow
- 2x failure_to_complete_task
- 1x crm_verification_failure

## Scenario Verdicts

- FAIL: booking_happy_path_full (19 findings)
- FAIL: booking_missing_name (23 findings)
- FAIL: booking_missing_phone (1 findings)
- PASS: booking_conflict_slot (0 findings)
- PASS: booking_interrupted_then_resume (0 findings)
- PASS: booking_user_changes_time_mid_flow (0 findings)
- PASS: faq_then_booking (0 findings)
- PASS: booking_with_short_affirmations (0 findings)
- FAIL: booking_with_fragmented_inputs (1 findings)
- FAIL: booking_with_colloquial_ptbr (7 findings)
- FAIL: reschedule_happy_path (5 findings)
- PASS: reschedule_conflict (0 findings)
- PASS: reschedule_missing_time (0 findings)
- FAIL: reschedule_interrupted_then_resume (5 findings)
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (4 findings)
- PASS: generated_i0001_02_seed_cancellation_colloquial (0 findings)
- PASS: generated_i0001_03_seed_booking_with_faq_interruption (0 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (7 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (5 findings)
