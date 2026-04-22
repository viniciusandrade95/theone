# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T20:58:09.249553+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 5x booking happy_path crm_side_effect: expected matching appointment to exist
- 5x reschedule happy_path crm_side_effect requires_existing_appointment: expected status completed, got response=ok workflow=awaiting_target_reference
- 5x reschedule happy_path crm_side_effect requires_existing_appointment: reply missing any expected text: remarcação, remarcado, confirmada, confirmado
- 5x reschedule happy_path crm_side_effect requires_existing_appointment: Slot loss detected: time
- 5x ambiguous booking generated missing_time: workflow appears to have reset to collecting with empty slots

## Most Frequent Bugs

- 10x execution.crm_ambiguous_expected
- 10x conversation.state_reset
- 5x execution.crm_rejected
