# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260422T171924Z-b665a5e3
- Mode: hybrid
- Started: 2026-04-22T17:19:24.033542+00:00
- Completed: 2026-04-22T17:19:55.663112+00:00
- Total scenarios: 19
- Pass: 0
- Fail: 19
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 6x booking fragmented state: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","
- 6x booking fragmented state: expected route workflow, got None
- 6x booking fragmented state: expected workflow book_appointment, got None
- 5x booking missing_phone guardrail: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Chatbot service request failed","
- 5x booking missing_phone guardrail: expected route workflow, got None

## Top Failure Types

- 167x conversation.state_reset
- 62x execution.runtime_internal_error
- 16x evaluator.wrong_expected_status
- 9x conversation.reference_disambiguation_failed
- 5x conversation.correction_mishandled
- 3x execution.identity_missing_block_expected
- 1x execution.crm_rejected

## Scenario Verdicts

- FAIL: booking_happy_path_full (17 findings)
- FAIL: booking_missing_name (26 findings)
- FAIL: booking_missing_phone (38 findings)
- FAIL: booking_conflict_slot (9 findings)
- FAIL: booking_interrupted_then_resume (12 findings)
- FAIL: booking_user_changes_time_mid_flow (16 findings)
- FAIL: faq_then_booking (7 findings)
- FAIL: booking_with_short_affirmations (7 findings)
- FAIL: booking_with_fragmented_inputs (40 findings)
- FAIL: booking_with_colloquial_ptbr (9 findings)
- FAIL: reschedule_happy_path (12 findings)
- FAIL: reschedule_conflict (4 findings)
- FAIL: reschedule_missing_time (6 findings)
- FAIL: reschedule_interrupted_then_resume (14 findings)
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (8 findings)
- FAIL: generated_i0001_02_seed_cancellation_colloquial (6 findings)
- FAIL: generated_i0001_03_seed_booking_with_faq_interruption (10 findings)
- FAIL: generated_i0001_04_seed_colloquial_fragmented_booking (11 findings)
- FAIL: generated_i0001_05_seed_missing_time_booking (11 findings)
