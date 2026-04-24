# Sidequest focus pack

Latest run:
`/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_local_20260422_031211`

Latest autonomous iteration:
`/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_local_20260422_031211/autonomous/iterations/0006-20260422T021620Z-78194a6c`

Focus folder:
`/home/vinicius/system-audit/workspace/theone/docs/test_runs/sidequest_focus_20260422_033842`

## Target

Fix only this family:

- Repeated date question
- conversation.slot_loop
- conversation.state_reset
- conversation.short_confirmation_misrouted
- conversation.time_flexible_mishandled

Ignore for now:

- crm_side_effect
- execution.crm_ambiguous_expected
- evaluator.layer_mixing unless directly caused by real workflow bug

## top_failures.md

# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T02:16:10.920675+00:00
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

## Copied scenario files

docs/test_runs/sidequest_focus_20260422_033842/booking_happy_path_full.json
docs/test_runs/sidequest_focus_20260422_033842/booking_interrupted_then_resume.json
docs/test_runs/sidequest_focus_20260422_033842/booking_missing_phone.json
docs/test_runs/sidequest_focus_20260422_033842/booking_with_fragmented_inputs.json
docs/test_runs/sidequest_focus_20260422_033842/booking_with_short_affirmations.json
