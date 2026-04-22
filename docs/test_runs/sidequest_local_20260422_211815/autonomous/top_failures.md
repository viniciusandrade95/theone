# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T20:22:29.912582+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 5x booking happy_path crm_side_effect: reply missing any expected text: registr, agend, pré-agendamento, confirm
- 5x booking happy_path crm_side_effect: expected matching appointment to exist
- 5x booking missing_data guardrail: expected status awaiting_confirmation, got response=ok workflow=collecting
- 5x booking missing_phone guardrail: expected status awaiting_confirmation, got response=ok workflow=collecting
- 5x booking fragmented state: reply missing any expected text: registr, agend, pré-agendamento, confirm

## Most Frequent Bugs

- 15x evaluator.layer_mixing
- 15x conversation.state_reset
- 10x execution.identity_missing_block_expected
- 10x conversation.slot_loop
- 10x execution.crm_ambiguous_expected
- 10x conversation.short_confirmation_misrouted
- 10x conversation.time_flexible_mishandled
- 5x execution.crm_rejected
