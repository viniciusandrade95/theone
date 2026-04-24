# Sidequest focus pack

## Latest run

/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_local_20260422_034420

## Latest autonomous iteration

/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_local_20260422_034420/autonomous/iterations/0006-20260422T024831Z-40936afe

## Focus folder

/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219

## Target failures

Fix only this family:

- booking missing_phone guardrail: Repeated date question
- booking fragmented state: Repeated date question
- conversation.slot_loop
- conversation.state_reset
- conversation.short_confirmation_misrouted
- conversation.time_flexible_mishandled

## Ignore for now

- booking happy_path crm_side_effect
- expected matching appointment to exist
- execution.crm_ambiguous_expected
- evaluator.layer_mixing unless it is directly caused by the real workflow bug

## Top failures

# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T02:48:21.217713+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 5x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 5x booking happy_path crm_side_effect: expected matching appointment to exist
- 5x booking missing_phone guardrail: Repeated date question
- 5x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 5x booking fragmented state: Repeated date question

## Most Frequent Bugs

- 15x evaluator.layer_mixing
- 15x conversation.slot_loop
- 15x conversation.state_reset
- 10x execution.crm_ambiguous_expected
- 10x conversation.short_confirmation_misrouted
- 10x conversation.time_flexible_mishandled
- 5x execution.crm_rejected

## Copied files

/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219/booking_happy_path_full.json
/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219/booking_interrupted_then_resume.json
/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219/booking_missing_phone.json
/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219/booking_with_fragmented_inputs.json
/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_repeated_date_20260422_035219/booking_with_short_affirmations.json
