# Codex Prompts — Assistant Communication and Measurement (2 weeks)

Date: 2026-04-12
Branch: `pm/assistant-foundation-week1-backlog`

This document turns the proposed PRs for the **Communication and Measurement** sprint into copy-pasteable prompts for Codex.

## Sprint goal
Industrialize the current assistant/outbound foundation so the product can:
- automatically confirm actions via SMS / Email / WhatsApp
- measure assistant activity and business outcomes
- expose a minimum funnel for messages, fallback, handoff, prebook, quote, consult, and conversion
- move outbound from manual assisted deeplink toward real provider-backed delivery lifecycle

## Existing repo context Codex must inspect and reuse
Codex should inspect the repository first and reuse existing patterns instead of inventing parallel architectures.

### Particularly relevant current capabilities
- WhatsApp inbound already has webhook verification, account routing, event dedupe, conversation persistence, and message persistence.
- Outbound already has templates, preview, send, resend, history, and CRM interaction creation, but it is currently WhatsApp-deeplink-assisted rather than provider-confirmed.
- Assistant session / prebook persistence already exists.
- Analytics endpoints already exist for booking/business metrics, but not yet for assistant funnel / ROI.
- Multitenancy is enforced by header/context and must remain strict in all new reads/writes.

### Files/areas Codex should inspect before coding
At minimum, inspect files equivalent to:
- `app/http/routes/outbound.py`
- `modules/messaging/repo/outbound_sql.py`
- `modules/messaging/models/outbound_message_orm.py`
- `modules/messaging/models/message_template_orm.py`
- `app/http/routes/messaging.py`
- `modules/messaging/service/inbound_webhook_service.py`
- `modules/messaging/models/message_orm.py`
- `modules/messaging/models/webhook_event_orm.py`
- `app/http/routes/analytics.py`
- `app/http/routes/chatbot.py`
- `app/http/routes/assistant_prebook.py`
- `.env.example`
- existing docs under `docs/features/*` and `docs/planning/*`

## Important product/technical constraints
- Do **not** keep pretending `sent` means provider delivery confirmation. Introduce a real delivery lifecycle.
- Do **not** create a second messaging model parallel to the existing one. Extend the current outbound path cleanly.
- Do **not** overbuild marketing automation, journey builder, or BI platforms in this sprint.
- Do **not** weaken multitenancy or introduce unscoped callbacks/webhooks.
- Keep provider abstraction thin and pragmatic.
- Prefer robust minimal architecture over many provider-specific branches.
- Preserve current error conventions and current route boundaries where reasonable.

---

# PR 1 — Provider-backed outbound core

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to implement the **provider-backed outbound core** so the current outbound module can move from WhatsApp deeplink-assisted sending to real delivery-oriented outbound communication with lifecycle tracking.

### Product goal
The product currently supports outbound templates, preview, manual send initiation, resend, and history. This PR must upgrade the outbound core so the system can support real provider-backed delivery status and serve as the base for automatic confirmations in later PRs.

### Critical context
The repository already has a stronger inbound messaging model than outbound:
- inbound has verified webhooks, account routing, deduped webhook events, conversations, and messages
- outbound currently stores outbound message history but treats `sent` as a user-assisted action rather than confirmed provider delivery

This PR should **industrialize outbound using the current patterns that already work in inbound**, without duplicating the messaging domain.

### Required deliverables
1. Expand outbound persistence so outbound messages can support real provider lifecycle.
2. Introduce a thin outbound provider abstraction.
3. Implement at least one real provider-backed outbound path in architecture shape, with clean extension points for SMS / Email / WhatsApp.
4. Add delivery status callback / event ingestion path(s).
5. Update tests and docs.

### What Codex should implement
#### A. Extend outbound message model
Expand the outbound message model/repo to support, at minimum, fields like:
- provider
- provider_message_id
- recipient
- delivery_status
- delivery_status_updated_at
- error_code
- idempotency_key
- trigger_type
- trace_id
- conversation_id
- assistant_session_id
- scheduled_for
- delivered_at
- failed_at

You may refine field names after inspecting the repo, but the resulting model must support real delivery lifecycle and later assistant funnel attribution.

#### B. Add outbound delivery event persistence
Create a delivery event table/model to capture provider callbacks / status events. It should support dedupe and tenant-safe updates.

Suggested fields include:
- tenant_id
- provider
- external_event_id
- provider_message_id
- channel
- status
- payload
- received_at

#### C. Introduce provider abstraction
Create a thin provider interface and concrete adapters for channels. Keep this pragmatic.

A reasonable shape is:
- base protocol/interface for send
- channel/provider implementations under `modules/messaging/providers/*`
- orchestration service that:
  - resolves template + rendered body
  - creates outbound message record
  - sends via provider
  - persists provider ids/statuses

You do **not** need a sophisticated plugin system. Keep it robust and minimal.

#### D. Add callback/status ingestion path
Implement route/service logic to ingest provider delivery status callbacks/events safely.

Requirements:
- tenant-safe association to outbound message
- idempotent handling of duplicate callbacks
- safe status transitions
- event persistence for troubleshooting

### Critical robustness requirements
- Preserve multitenancy in all message and callback paths.
- Do not allow a callback to update another tenant's outbound message.
- Keep idempotency for send and callback handling where practical.
- Do not break existing outbound preview / history use cases.
- Maintain backwards compatibility as much as possible, but prefer correctness over preserving misleading `sent` semantics.
- If introducing enum-like statuses, keep them explicit and finite.

### Testing requirements
Add or update tests covering at least:
- outbound message creation with expanded fields
- provider send success path
- provider send failure path
- callback/status update success path
- duplicate callback handling
- tenant-safe callback handling
- no regression for current preview/send/history behaviors where still supported

### Documentation requirements
Update docs to explain:
- new outbound lifecycle semantics
- difference between queued/sent/delivered/failed states
- provider-backed flow vs previous deeplink-assisted MVP behavior
- callback processing model
- any environment variables required for provider-backed outbound

### Deliverable format
Please:
- create a focused branch for this PR
- inspect current outbound and inbound messaging architecture first
- implement the smallest robust change set that enables provider-backed outbound lifecycle
- add tests and docs
- summarize changed files, migrations, behavior changes, and follow-up risks

---

# PR 2 — Automatic confirmations via SMS / Email / WhatsApp

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to implement **automatic confirmations** so the system can confirm assistant/business actions via SMS, Email, and WhatsApp.

### Product goal
When key actions happen, the product should automatically send confirmations rather than relying only on manual staff action. This is the first meaningful automation layer on top of the newly industrialized outbound core.

### Critical constraints
- Keep the trigger set intentionally small.
- Reuse the existing outbound templates model where possible.
- Do not build a full journey builder or campaign system in this PR.
- Preserve tenant isolation and existing action semantics.
- Be robust to missing customer channel data and provider failures.

### Required deliverables
1. Introduce a minimal automatic confirmation orchestration service.
2. Trigger automatic confirmations for the most important assistant/business outcomes.
3. Support channel-aware sending for SMS / Email / WhatsApp.
4. Add fallback/selection behavior when the preferred channel is unavailable.
5. Update tests and docs.

### Minimum triggers this PR should support
Support automatic confirmations for at least these events if the corresponding domain objects already exist in the repo/near-term implementation:
- prebook created
- handoff created
- quote created
- consult created

If quote / consult / handoff are not all fully present in current code, inspect the current repo state and implement only what is real and safe now, while leaving the orchestration extensible for the remaining ones.

### Suggested implementation shape
- a service such as `AssistantCommunicationService` or similar
- channel resolution logic using available customer data (phone/email) and message template type/channel
- event-to-template mapping for confirmations
- outbound message creation + send through the provider-backed outbound core

### Channel behavior expectations
- WhatsApp confirmation when valid WhatsApp/phone path exists
- SMS confirmation when SMS path exists
- Email confirmation when email path exists
- graceful fallback behavior when the first-choice channel is not usable

The code should clearly document and implement a deterministic fallback order.

### Robustness requirements
- If the customer lacks a usable phone or email, fail gracefully and persist useful status/error context.
- Do not send the same confirmation repeatedly on duplicate events.
- Make event triggering idempotent where practical.
- Keep confirmation templates explicit and type-safe enough to audit.
- Ensure confirmation sends are attributable to the originating action (`trigger_type`, trace correlation, related entity linkage, etc.).

### Testing requirements
Add or update tests covering at least:
- automatic confirmation on prebook created
- automatic confirmation on one additional supported event (handoff / quote / consult depending on actual repo state)
- fallback to alternate channel when preferred channel is unavailable
- graceful failure when no viable recipient channel exists
- idempotent-ish duplicate event handling
- tenant-safe confirmation sends

### Documentation requirements
Update docs to explain:
- which events trigger automatic confirmations
- how channel selection/fallback works
- what template/channel combinations are supported
- how failures are recorded and surfaced operationally

### Deliverable format
Please:
- create a focused branch for this PR
- inspect existing outbound templates and related assistant/business events first
- implement the smallest robust automation layer for confirmations
- add tests and docs
- summarize assumptions, unsupported edge cases, and future expansion paths

---

# PR 3 — Assistant analytics, telemetria, and minimum funnel

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to implement **assistant analytics and minimum funnel tracking** so the product can measure assistant ROI and business movement from conversation to result.

### Product goal
The system must be able to measure, at minimum:
- messages
- fallback
- handoff
- prebook
- quote
- consult
- conversion

This must produce assistant-specific analytics rather than relying only on booking analytics.

### Critical constraints
- Do not confuse technical telemetry with business funnel events. Both matter, but keep them conceptually separate.
- Keep the assistant funnel event taxonomy explicit and finite.
- Do not build a full external BI stack in this PR.
- Do not depend on inferred text-only states when a persisted business artifact exists.
- Preserve tenant isolation in every event write and every analytics query.

### Required deliverables
1. Create a persistence layer for assistant funnel events.
2. Instrument assistant/business paths to emit funnel events.
3. Add assistant analytics endpoints for overview/funnel/channel/template/conversion views.
4. Add light technical telemetry where useful to support communication ROI and operational debugging.
5. Update tests and docs.

### Funnel event model requirements
Create a model/table such as `assistant_funnel_events` with fields sufficient for attribution, for example:
- tenant_id
- trace_id
- conversation_id
- assistant_session_id
- customer_id
- event_name
- event_source
- channel
- related_entity_type
- related_entity_id
- metadata
- created_at

You may adapt naming after inspecting current repo conventions, but the model must support business attribution.

### Minimum event taxonomy to support
Implement explicit business funnel events for at least:
- assistant_message_received
- assistant_message_replied
- assistant_fallback
- assistant_handoff_requested
- assistant_handoff_created
- assistant_prebook_requested
- assistant_prebook_created
- assistant_quote_requested
- assistant_quote_created
- assistant_consult_requested
- assistant_consult_created
- assistant_conversion_confirmed

If quote / consult / handoff are not all fully implemented yet in the repository, instrument what is real now and structure the event taxonomy so the missing events can be added cleanly.

### Analytics endpoint expectations
Add assistant-focused analytics endpoints, for example under `/analytics/assistant/*`, such as:
- overview
- funnel
- channels
- templates
- conversions

The resulting API should enable ROI-style questions such as:
- how many assistant messages came in?
- how many fell back?
- how many became handoff / prebook / quote / consult?
- how many converted?
- which channels/templates/providers perform best?

### Technical telemetry expectations
Where useful, add supporting telemetry for:
- outbound send success/failure by channel/provider
- delivery success/failure by channel/provider
- callback latency / event processing outcomes

Keep metric/log label cardinality controlled.

### Robustness requirements
- Funnel event writes must be tenant-safe.
- Avoid double-counting on duplicate requests/callbacks wherever practical.
- Preserve trace correlation through assistant, outbound, and conversion-related flows.
- Keep event names explicit and stable.
- Prefer persisted artifact attribution (real handoff/prebook/etc.) over text-only inference whenever available.

### Testing requirements
Add or update tests covering at least:
- funnel event persistence
- emission of message / fallback / prebook events
- one or more additional artifact-backed events depending on repo state
- analytics endpoint aggregation correctness
- no cross-tenant leakage in analytics results
- duplicate or retry handling where relevant

### Documentation requirements
Update docs to explain:
- event taxonomy
- analytics endpoint purpose and output shape
- difference between funnel events and technical telemetry
- how ROI-style metrics should be interpreted

### Deliverable format
Please:
- create a focused branch for this PR
- inspect current assistant, outbound, and analytics flows first
- implement the smallest robust analytics/funnel foundation that answers product ROI questions
- add tests and docs
- summarize event taxonomy decisions, query tradeoffs, and future BI expansion considerations

---

# PR 4 — Hardening, integration coverage, and ROI readiness

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to add **integration hardening and ROI-readiness validation** for the communication and measurement sprint.

### Product goal
By the end of this PR, the repository should prove—through robust integration coverage and targeted hardening—that:
- automatic confirmations work across the supported communication flows
- outbound delivery lifecycle behaves correctly enough for production rollout
- assistant funnel analytics can support ROI conversations with confidence

### Critical constraints
- Do not introduce a huge new test stack if strong API/integration tests are already the project norm.
- Focus on meaningful end-to-end/integration validation of business flows and messaging lifecycle.
- Preserve multitenancy and avoid flaky time/provider-dependent tests.

### Required deliverables
1. Add integration coverage across the communication + measurement flow.
2. Harden status transitions, retries, duplicate handling, and analytics consistency where needed.
3. Apply small bug fixes or API consistency improvements uncovered by integrated testing.
4. Update runbook/docs for rollout and validation.

### Minimum integration scenarios to validate
Cover realistic flows such as:
1. **Prebook confirmation flow**
   - assistant/business event occurs
   - confirmation is triggered
   - outbound message is created
   - provider send succeeds or fails deterministically in test
   - lifecycle/status updates are reflected
   - funnel event(s) are emitted
2. **Handoff confirmation flow**
   - handoff artifact created
   - customer confirmation sent
   - internal visibility or related side effect remains intact
   - funnel event(s) recorded
3. **Analytics/ROI consistency flow**
   - representative assistant/business actions happen
   - analytics endpoints reflect expected counts/rates
4. **Duplicate/callback safety flow**
   - duplicate status callback does not break counts or message lifecycle
   - duplicate trigger does not create uncontrolled duplicate communication

### Hardening expectations
You should inspect the integrated behavior and tighten areas such as:
- callback status transition safety
- retry / duplicate handling
- idempotency around action-triggered confirmations
- analytics event double-count prevention
- tenant-safe linkage of provider callbacks
- graceful failure behavior when channels/providers are unavailable

### Testing requirements
Add or update integration tests covering at least:
- communication trigger -> outbound record -> delivery status update
- funnel event consistency with communication side effects
- analytics endpoint consistency after seeded flows
- duplicate callback/duplicate trigger safety
- cross-tenant safety in the tested flows

### Documentation requirements
Update docs to explain:
- how to validate the sprint end-to-end locally
- rollout/ops considerations
- what statuses and analytics indicate success vs failure
- known limitations that remain outside the sprint

### Deliverable format
Please:
- create a focused branch for this PR
- inspect the existing integration test style in the repo first
- implement robust integration coverage and small targeted hardening changes
- update docs/runbook material
- summarize what is now validated end-to-end, what remains partial, and what should be addressed next

---

## Optional reusable tail for every prompt

If you want a reusable final instruction to append to each Codex prompt, use this:

> Before changing code, inspect the current implementation and explain the relevant architecture for this PR. Then implement the smallest robust change set that satisfies the product goal while preserving multitenancy, current error conventions, and current route boundaries where possible. Add tests for success paths, failure paths, duplicate/retry behavior, and tenant-safety where relevant. Update docs. At the end, summarize changed files, migrations, tests added, tradeoffs, and follow-up risks.
