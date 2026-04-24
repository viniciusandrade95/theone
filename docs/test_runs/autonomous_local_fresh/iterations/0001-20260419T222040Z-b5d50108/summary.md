# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T222040Z-b5d50108
- Mode: hybrid
- Started: 2026-04-19T22:20:40.760896+00:00
- Completed: 2026-04-19T22:21:38.865386+00:00
- Total scenarios: 19
- Pass: 0
- Fail: 19
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 6x booking fragmented state: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- 6x booking fragmented state: expected route workflow, got None
- 6x booking fragmented state: expected workflow book_appointment, got None
- 5x booking missing_phone guardrail: HTTP request failed with status 500: {"error":"INTERNAL_ERROR"}
- 5x booking missing_phone guardrail: expected route workflow, got None

## Top Failure Types

- 197x assertion_failure
- 62x upstream_runtime_failure
- 3x failure_to_complete_task
- 1x crm_verification_failure

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
