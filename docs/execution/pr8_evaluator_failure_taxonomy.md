# PR8 - Evaluator Failure Taxonomy By Layer

## What Changed

The chatbot evaluator now keeps the legacy `category`, `type`, `message`, and `failures` fields, but enriches each failure record with:

- `failure_family`
- `failure_layer`

This allows reports to separate conversation bugs from execution/config/runtime and evaluator mistakes without breaking existing consumers.

## Families

Conversation:

- `conversation.state_reset`
- `conversation.slot_loop`
- `conversation.correction_mishandled`
- `conversation.short_confirmation_misrouted`
- `conversation.reference_disambiguation_failed`
- `conversation.time_flexible_mishandled`

Execution:

- `execution.identity_missing_block_expected`
- `execution.service_mapping_missing`
- `execution.crm_ambiguous_expected`
- `execution.crm_rejected`
- `execution.runtime_internal_error`

Evaluator:

- `evaluator.wrong_expected_status`
- `evaluator.layer_mixing`

## Before / After

Before:

```json
{
  "category": "assertion_failure",
  "message": "workflow appears to have reset to collecting with empty slots",
  "step_index": 1
}
```

After:

```json
{
  "category": "assertion_failure",
  "message": "workflow appears to have reset to collecting with empty slots",
  "step_index": 1,
  "failure_family": "conversation.state_reset",
  "failure_layer": "conversation"
}
```

Config/runtime example:

```json
{
  "category": "assertion_failure",
  "message": "expected status awaiting_confirmation, got response=ok workflow=failed",
  "failure_family": "execution.service_mapping_missing",
  "failure_layer": "execution"
}
```

## Evaluator Behavior

- A workflow reaching `completed` after an explicit final confirmation such as `ok`, `sim`, or `pode confirmar` is no longer automatically marked as a failure when a generated scenario had a stale `expected_final_status=awaiting_confirmation`.
- `config_missing_services_json` and related service mapping failures are classified as `execution.service_mapping_missing`.
- `appointment_ambiguous` is classified as `execution.crm_ambiguous_expected`, so it is visible as a reference-resolution stage instead of being mixed with state-reset bugs.
