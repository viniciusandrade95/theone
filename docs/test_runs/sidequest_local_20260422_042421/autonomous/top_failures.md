# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T03:28:22.283636+00:00
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
