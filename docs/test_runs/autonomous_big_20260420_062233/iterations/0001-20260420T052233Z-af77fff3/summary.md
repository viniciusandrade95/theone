# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260420T052233Z-af77fff3
- Mode: hybrid
- Started: 2026-04-20T05:22:33.871471+00:00
- Completed: 2026-04-20T05:23:37.089989+00:00
- Total scenarios: 26
- Pass: 0
- Fail: 26
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 12x ambiguous generated reschedule: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 12x ambiguous generated reschedule: expected workflow reschedule_appointment, got None
- 10x booking faq generated interruption: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 10x booking correction fragmented generated ptbr: HTTP request failed with status 400: {"error":"VALIDATION_ERROR","details":{"message":"Missing tenant header: X-Tenant-I
- 10x booking correction fragmented generated ptbr: expected workflow book_appointment, got None

## Top Failure Types

- 225x assertion_failure
- 91x upstream_runtime_failure
- 6x failure_to_complete_task
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
- FAIL: generated_i0001_06_seed_reschedule_ambiguous (8 findings)
- FAIL: generated_i0001_07_seed_cancellation_colloquial (6 findings)
- FAIL: generated_i0001_08_seed_booking_with_faq_interruption (10 findings)
- FAIL: generated_i0001_09_seed_colloquial_fragmented_booking (11 findings)
- FAIL: generated_i0001_10_seed_missing_time_booking (11 findings)
- FAIL: generated_i0001_11_seed_reschedule_ambiguous (8 findings)
- FAIL: generated_i0001_12_seed_cancellation_colloquial (6 findings)
