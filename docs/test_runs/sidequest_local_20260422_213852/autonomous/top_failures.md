# Autonomous Chatbot Top Failures

- Updated: 2026-04-22T20:43:07.523887+00:00
- Iterations tracked: 5

## Top 5 Failure Patterns

- 5x booking happy_path crm_side_effect: expected matching appointment to exist
- 5x booking ptbr nlu colloquial: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- 5x booking ptbr nlu colloquial: Repeated time question
- 5x reschedule happy_path crm_side_effect requires_existing_appointment: expected status completed, got response=ok workflow=awaiting_target_reference
- 5x reschedule happy_path crm_side_effect requires_existing_appointment: reply missing any expected text: remarcação, remarcado, confirmada, confirmado

## Most Frequent Bugs

- 10x execution.crm_ambiguous_expected
- 10x conversation.state_reset
- 5x execution.crm_rejected
- 5x evaluator.layer_mixing
- 5x conversation.time_flexible_mishandled
