# Chatbot Autonomous Tester Summary

- Iteration: 1
- Run ID: 20260419T141238Z-14d5bcfd
- Mode: hybrid
- Started: 2026-04-19T14:12:38.474893+00:00
- Completed: 2026-04-19T14:16:01.076259+00:00
- Total scenarios: 16
- Pass: 0
- Fail: 16
- Partial: 0
- Generation: FALLBACK

## Top 5 Failure Patterns

- 6x booking fragmented state: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name
- 6x booking fragmented state: response body is not a JSON object
- 6x booking fragmented state: expected route workflow, got None
- 6x booking fragmented state: expected workflow book_appointment, got None
- 5x booking missing_phone guardrail: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name

## Top Failure Types

- 183x assertion_failure
- 94x upstream_runtime_failure
- 1x crm_verification_failure

## Scenario Verdicts

- FAIL: booking_happy_path_full (19 findings)
- FAIL: booking_missing_name (30 findings)
- FAIL: booking_missing_phone (43 findings)
- FAIL: booking_conflict_slot (11 findings)
- FAIL: booking_interrupted_then_resume (15 findings)
- FAIL: booking_user_changes_time_mid_flow (19 findings)
- FAIL: faq_then_booking (10 findings)
- FAIL: booking_with_short_affirmations (9 findings)
- FAIL: booking_with_fragmented_inputs (46 findings)
- FAIL: booking_with_colloquial_ptbr (12 findings)
- FAIL: reschedule_happy_path (14 findings)
- FAIL: reschedule_conflict (5 findings)
- FAIL: reschedule_missing_time (7 findings)
- FAIL: reschedule_interrupted_then_resume (17 findings)
- FAIL: generated_i0001_01_seed_reschedule_ambiguous (12 findings)
- FAIL: generated_i0001_02_seed_cancellation_colloquial (9 findings)
