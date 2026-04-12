# Assistant — Quick Product Wins (2 weeks)

Date: 2026-04-12
Owner suggestion: PM + Backend + Frontend + QA
Status: proposed
Branch: `pm/assistant-foundation-week1-backlog`

## Goal

Deliver a thin but useful product increment in 2 weeks so that the assistant can:
- suggest real available slots automatically
- hand off to a human agent
- persist intent and basic conversational history
- pass E2E flows for:
  - "usuário pediu horário"
  - "quero falar com atendente"

## Why this fits now

This fits because the repo already contains enough primitives to avoid building from scratch:
- public availability route already exists
- assistant session persistence already exists
- chatbot normalized response already supports `intent` and `handoff.requested`
- CRM interactions already exist and can be used as MVP ticket trail

This means the product win can be shipped as a thin orchestration layer, instead of a full new domain subsystem.

---

## Current repo state that makes this possible

### Already available
- `POST /api/chatbot/message`
- `POST /api/chatbot/reset`
- `GET /public/book/{slug}/availability`
- chatbot conversation/session persistence via `chatbot_conversation_sessions`
- normalized chatbot response already exposes `intent` and `handoff`
- CRM interaction creation already exists and is tenant-safe

### Important current limitations
- there is no first-class handoff aggregate yet
- assistant persistence today is session-level, not message-history-level
- there is no dedicated internal notification system yet
- there are no existing E2E tests for the two target product flows

---

## Product outcome expected at the end

At the end of the 2 weeks, the assistant should be able to:

### Flow 1 — User asked for a time slot
- understand the user intent as booking/availability intent
- resolve context enough to query real availability
- suggest 3 to 5 real slots from existing availability endpoints
- keep the booking intent and minimal conversation context persisted
- let the next assistant turn continue from the same context

### Flow 2 — I want to talk to an attendant
- recognize explicit handoff intent
- create an internal handoff record using MVP storage
- create an operational CRM interaction/timeline entry
- surface a clear assistant response saying a human will follow up
- trigger at least one internal notification path in MVP form

---

## MVP product decisions

### Decision 1 — Slot finding should reuse existing availability route
Do **not** build a second availability engine.

Use the existing public booking availability route as the system of record for slot suggestions. The assistant orchestration layer should resolve the correct tenant/booking slug/service/location/date and then consume that route.

### Decision 2 — Handoff should be a thin MVP, not a full queue system
Do **not** wait for full handoff domain design.

For this 2-week increment:
- create a dedicated assistant handoff/ticket record
- also write a CRM interaction for operational visibility
- expose a minimal internal listing/notification path

### Decision 3 — Intent/history persistence should be lightweight
Do **not** implement full chat transcript infra unless strictly needed.

Persist:
- latest recognized intent
- conversation context for slot finding / handoff continuation
- enough message history to continue the flow coherently

This can be minimal and still unlock product value.

---

## Delivery streams

## Stream 1 — Automatic slot finding

### Ticket P1 — Define assistant slot-finding request/response contract
**Type:** product contract
**Priority:** P0

**Tasks**
- Define a backend contract for assistant slot finding.
- Input should allow:
  - `conversation_id`
  - `session_id`
  - `customer_id` (nullable)
  - `service_id` or service hint
  - `location_id` (nullable)
  - `date` or natural-language-derived target date
  - `timezone` (nullable)
- Output should include:
  - `status`
  - `resolved_service_id`
  - `resolved_location_id`
  - `date`
  - `timezone`
  - `slots[]`
  - `slot_count`
  - `trace_id`

**Files impacted**
- `modules/assistant/contracts/slot_finding.py`
- `frontend/lib/contracts/assistant.ts`
- docs for assistant contracts

**Acceptance criteria**
- Contract is stable enough for frontend and tests.
- It is explicit which fields are resolved by the backend and which must come from the assistant/context.

---

### Ticket P2 — Build slot-finding service on top of existing availability endpoint
**Type:** backend orchestration
**Priority:** P0

**Tasks**
- Create a thin service that reuses existing booking availability source of truth.
- Resolve required booking settings / slug / location / service.
- Query existing availability and normalize into assistant-friendly slot suggestions.
- Return the first useful set of real slots.

**Files impacted**
- new assistant service file, e.g. `modules/assistant/service/slot_finding_service.py`
- `app/http/routes/chatbot.py` or a new assistant operational route
- possibly helper calls into booking/public booking code

**Acceptance criteria**
- For a valid service/date combination, assistant can return real slots.
- Suggested slots come from the existing availability logic, not duplicated business rules.
- Empty availability is returned as a clean assistant outcome, not as a crash.

**Tests**
- service tests for slot finding
- API test with seeded service/location/availability data

---

### Ticket P3 — Assistant orchestration for booking-intent turns
**Type:** assistant behavior
**Priority:** P0

**Tasks**
- Extend assistant flow so booking intent can trigger slot lookup when enough context is available.
- Support at least these states:
  - insufficient info -> ask follow-up question
  - enough info -> fetch slots
  - no slots -> propose next day / alternative outcome
- Persist resolved booking context in conversation history/state.

**Files impacted**
- `app/http/routes/chatbot.py`
- new assistant orchestration service/module
- frontend assistant page if quick UI support is added

**Acceptance criteria**
- Assistant can move from user request to concrete slot suggestions in one or more turns.
- Follow-up questions are deterministic when service/date/location is missing.
- Booking context survives the next message turn.

**Tests**
- API tests for "missing service", "missing date", "slots found", "no slots"

---

## Stream 2 — Handoff to humans (MVP)

### Ticket H1 — Create handoff MVP data model
**Type:** backend/domain MVP
**Priority:** P0

**Tasks**
- Introduce a lightweight persistence model for assistant handoff requests.
- Suggested fields:
  - `id`
  - `tenant_id`
  - `conversation_id`
  - `session_id`
  - `customer_id`
  - `status` (`open`, `claimed`, `closed`)
  - `reason`
  - `summary`
  - `requested_by`
  - `created_at`
  - `updated_at`
- Keep it small; do not build full queueing/SLA logic yet.

**Files impacted**
- `modules/assistant/models/*` new handoff ORM
- `alembic/versions/<new>_add_assistant_handoffs.py`
- `modules/assistant/repo/*`

**Acceptance criteria**
- Handoff requests can be created and listed.
- Handoff record is tenant-scoped.

**Tests**
- repo CRUD tests
- migration tests

---

### Ticket H2 — Create handoff API/action path
**Type:** backend/product MVP
**Priority:** P0

**Tasks**
- Add a backend path that creates a handoff request from assistant context.
- It should accept conversation/session/customer/reason/summary.
- It should return a user-safe confirmation payload.

**Files impacted**
- `app/http/routes/chatbot.py` or new `app/http/routes/assistant_handoff.py`
- new assistant handoff service/repo

**Acceptance criteria**
- Explicit handoff requests create a persistent record.
- The assistant can answer: "Vou encaminhar para um atendente" with a real backend side effect.

**Tests**
- API tests for handoff creation
- tenant scoping tests

---

### Ticket H3 — Write CRM interaction on handoff creation
**Type:** backend operational visibility
**Priority:** P0

**Tasks**
- On handoff creation, also write a CRM interaction using existing CRM interaction capability.
- Suggested interaction type:
  - `assistant_handoff`
- Include reason + short summary in content.

**Files impacted**
- handoff service
- CRM service integration path

**Acceptance criteria**
- Customer timeline shows that assistant escalated to human.
- Operations can discover the handoff even without a dedicated handoff UI.

**Tests**
- API test asserting both handoff record and CRM interaction are created

---

### Ticket H4 — Add internal notification path (thin MVP)
**Type:** product/ops MVP
**Priority:** P1

**Tasks**
- Implement one internal notification path for new handoffs.
- MVP options, choose one:
  - dashboard list/pending handoffs endpoint
  - outbound internal note record
  - email/slack-style integration placeholder if infra already exists
- Do not overbuild. A visible "pending handoffs" list is enough for MVP.

**Files impacted**
- new route for listing open handoffs
- frontend dashboard widget/page if chosen

**Acceptance criteria**
- A staff user can discover new handoff requests without database inspection.
- New handoff becomes operationally visible within the product.

**Tests**
- API test for listing open handoffs
- frontend smoke test if UI is added

---

## Stream 3 — Intent persistence and assistant history

### Ticket S1 — Extend assistant session persistence with latest intent/state
**Type:** backend persistence
**Priority:** P0

**Problem**
Current assistant persistence is session metadata only, not intent-aware conversation state.

**Tasks**
- Extend conversation session storage with lightweight state fields such as:
  - `last_intent`
  - `last_intent_confidence` (optional)
  - `state_payload` / `context_payload` JSON
- Use this to persist booking resolution context and handoff context.

**Files impacted**
- `modules/chatbot/models/conversation_session_orm.py`
- `modules/chatbot/repo/session_repo.py`
- migration file

**Acceptance criteria**
- Latest assistant intent is queryable from persistence.
- Slot-finding and handoff can resume from persisted conversation state.

**Tests**
- repo tests for persisted state updates
- API tests across multiple turns

---

### Ticket S2 — Persist lightweight assistant message history
**Type:** backend persistence
**Priority:** P0

**Tasks**
- Add a lightweight message history table for assistant turns.
- Minimum fields:
  - `id`
  - `tenant_id`
  - `conversation_id`
  - `role` (`user`, `assistant`, `system`)
  - `message_text`
  - `intent` (nullable)
  - `created_at`
- Write one row for user turn and one for assistant reply.

**Files impacted**
- new ORM + repo + migration under chatbot/assistant module
- `app/http/routes/chatbot.py`

**Acceptance criteria**
- A conversation has real persisted turn history.
- History is enough to reconstruct recent assistant interactions for product support/debugging.

**Tests**
- repo tests for append/list history
- API tests for saved user+assistant turns

---

### Ticket S3 — Use persisted state/history in assistant follow-up turns
**Type:** assistant behavior
**Priority:** P1

**Tasks**
- On each new assistant turn, load conversation state/history.
- Use persisted context to avoid asking the same question again when slot-finding or handoff is in progress.
- Keep implementation intentionally shallow (recent turns + state only).

**Files impacted**
- `app/http/routes/chatbot.py`
- assistant orchestration service

**Acceptance criteria**
- Assistant remembers the booking context across turns.
- Assistant remembers that a handoff was already requested and does not duplicate it unnecessarily.

**Tests**
- multi-turn API tests

---

## Stream 4 — E2E coverage for the two target flows

### Ticket T1 — E2E: user asked for a time slot
**Type:** QA/E2E
**Priority:** P0

**Target scenario**
A user asks for an appointment time, assistant resolves enough context, fetches real slots, and returns them.

**Suggested script**
1. Seed tenant, booking settings, service, default/public location, available date.
2. Open assistant UI or run API-driven E2E flow.
3. Send a booking request phrase.
4. Ensure assistant either asks a missing-info question or returns real slots.
5. Complete follow-up turn if needed.
6. Assert the final response contains real slots from the booking source of truth.
7. Assert conversation state/history persisted.

**Acceptance criteria**
- Test is deterministic and green in CI/local runner.
- It validates real slot suggestion behavior, not only mock text.

---

### Ticket T2 — E2E: I want to talk to an attendant
**Type:** QA/E2E
**Priority:** P0

**Target scenario**
A user explicitly asks for a human agent; assistant creates a handoff and confirms the transfer.

**Suggested script**
1. Seed tenant and user/customer context.
2. Open assistant UI or run API-driven E2E flow.
3. Send a handoff phrase.
4. Assert assistant response confirms transfer.
5. Assert handoff record exists.
6. Assert CRM interaction exists.
7. Assert internal visibility path shows a pending handoff.

**Acceptance criteria**
- Test proves the handoff is not only textual; it must create a real backend artifact.

---

## Recommended PR structure

### PR 1 — Slot finding vertical slice
Includes:
- slot-finding contract
- slot-finding service reusing availability route
- assistant booking-intent orchestration
- tests for slot suggestion flow

### PR 2 — Handoff MVP vertical slice
Includes:
- handoff model/repo/migration
- handoff creation path
- CRM interaction side effect
- internal visibility MVP
- tests for handoff flow

### PR 3 — Persistence and conversation continuity
Includes:
- session state persistence
- assistant message history persistence
- multi-turn continuity logic
- tests for intent/history

### PR 4 — E2E and final polish
Includes:
- the two target E2E flows
- small UI polish in assistant page if needed
- bug fixes from integrated testing

---

## Two-week execution plan

### Week 1
- P1 contract for slot-finding
- P2 slot-finding service
- P3 booking-intent orchestration
- H1 handoff MVP model
- H2 handoff action path
- H3 CRM interaction side effect

### Week 2
- H4 internal visibility/notification MVP
- S1 session state persistence
- S2 assistant message history persistence
- S3 follow-up continuity logic
- T1 and T2 E2E flows
- hardening and bug fixes

---

## Definition of done

This 2-week increment is done only when:

1. Assistant can suggest real slots using existing availability logic.
2. Assistant can create a real handoff request to a human.
3. Handoff also creates a CRM interaction for operational visibility.
4. Latest intent and conversation context are persisted.
5. Basic assistant turn history is persisted.
6. Two E2E flows are green:
   - user asked for a time slot
   - user wants to talk to an attendant
7. Product demo shows actual backend side effects, not just assistant text.

---

## Suggested product demo

### Demo 1 — Slot suggestion
- Ask the assistant for a haircut tomorrow afternoon.
- Assistant resolves/asks missing info.
- Assistant returns 3 real available slots.
- Show persisted state/history in admin/debug view or DB-backed API output.

### Demo 2 — Human handoff
- Ask to speak to an attendant.
- Assistant confirms transfer.
- Show created handoff record.
- Show CRM interaction on customer timeline.
- Show pending handoff in internal visibility path.

---

## Risks

### Risk 1 — Slot-finding orchestration becomes a second booking engine
**Guardrail:** always reuse existing availability source of truth.

### Risk 2 — Handoff MVP grows into a full queue project
**Guardrail:** no SLA engine, no complex ownership workflow in this increment.

### Risk 3 — History persistence becomes full chat platform work
**Guardrail:** only store enough recent turns/state to support continuity and supportability.

---

## Post-increment follow-up
- richer handoff queue ownership and SLA rules
- quote and consult as first-class aggregates
- richer assistant UI for suggested slots and pending handoffs
- assistant tool authorization by intent/action
- analytics for assistant conversion to booking / handoff
