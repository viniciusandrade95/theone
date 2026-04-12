# Codex Prompts — Assistant Quick Product Wins (2 weeks)

Date: 2026-04-12
Branch: `pm/assistant-foundation-week1-backlog`
Related plan: `docs/planning/assistant-quick-product-wins-2weeks.md`

This document turns the proposed 4 PRs for the 2-week assistant product increment into copy-pasteable prompts for Codex.

## How to use these prompts

- Use **one prompt per PR**.
- Tell Codex to work on a **dedicated branch** per PR.
- Ask Codex to **inspect the repository first**, then implement.
- Require **tests**, **docs updates**, and **robustness guardrails** in every PR.
- Keep the implementation thin and aligned with the current repo architecture.

## Repo context Codex should rely on

Codex should discover and use these existing capabilities instead of rebuilding them:
- chatbot proxy endpoints already exist: `POST /api/chatbot/message`, `POST /api/chatbot/reset`
- public booking availability already exists and should remain the source of truth
- assistant session persistence already exists via `chatbot_conversation_sessions`
- chatbot normalized response already supports `intent` and `handoff.requested`
- CRM interactions already exist and can be reused for operational visibility
- multitenancy is header/context-based and must remain enforced in all new code paths
- audit/observability foundation may already be evolving in parallel; new product PRs must not regress that work

---

# PR 1 — Slot finding vertical slice

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to implement the **first vertical slice of assistant slot finding**, so that the assistant can suggest real appointment slots using the **existing booking availability source of truth**, without creating a second availability engine.

### Product goal
When a user asks for an appointment time, the assistant should be able to:
- understand this is a booking/availability intent
- resolve enough context to query real availability
- return 3 to 5 real slots when possible
- ask a deterministic follow-up question when required information is missing
- persist enough state so the next turn can continue naturally

### Critical constraints
- **Do not duplicate booking availability rules.** Reuse the existing availability logic or route as the system of record.
- **Do not build a full NLP stack.** Keep intent handling shallow and deterministic.
- **Do not overbuild orchestration.** This is a thin product slice.
- **Preserve multitenancy and existing auth behavior.**
- **Be robust** around missing inputs, no-availability scenarios, invalid service/location/date, and timezone handling.

### Existing repo context you must inspect and reuse
Please inspect these areas before coding:
- chatbot assistant route(s)
- public booking availability route and helpers
- booking settings / slug resolution
- assistant/chatbot session persistence
- normalized chatbot response format
- CRM customer context if needed
- tenant enforcement and current tests around chatbot and booking

At minimum, inspect files equivalent to:
- `app/http/routes/chatbot.py`
- `app/http/routes/public_booking.py`
- `modules/chatbot/repo/session_repo.py`
- `modules/chatbot/models/conversation_session_orm.py`
- existing assistant planning docs under `docs/planning/*`

### Required deliverables
1. A **slot-finding contract** for backend/frontend use.
   - Add a backend schema/module for slot-finding request/response.
   - Add or update frontend TypeScript contracts if needed.
2. A **thin slot-finding service** that resolves booking context and fetches real availability from the existing source of truth.
3. Assistant orchestration logic so booking-intent turns can:
   - ask for missing required info when needed
   - fetch slots when enough info exists
   - return a clean response if there are no slots
4. Persistence of minimal assistant state so follow-up turns can continue.
5. Tests and docs.

### Functional expectations
Support at least the following cases:
- User asks for a slot but does not specify the service -> assistant asks for service.
- User asks for a slot but does not specify the day/date -> assistant asks for date.
- User asks for a slot with enough context -> assistant returns real slots.
- No slots available -> assistant returns a helpful outcome and does not crash.
- Invalid service/location/date -> assistant returns a safe, deterministic validation outcome.

### Suggested implementation shape
You may choose the best fit after inspecting the repo, but the intended shape is:
- a new assistant service module, for example `modules/assistant/service/slot_finding_service.py`
- a contract module, e.g. `modules/assistant/contracts/slot_finding.py`
- minimal updates in the assistant/chatbot route layer to trigger slot finding when appropriate
- optional extension of conversation/session state persistence to remember booking context

### Robustness requirements
- Keep business logic centralized and avoid duplicating availability rules.
- Normalize timezones carefully.
- Guard against partial or stale session state.
- Never trust unscoped IDs across tenants.
- Use clear error handling and preserve current error response conventions.
- Avoid high-cardinality logging/metrics labels if touching observability.

### Testing requirements
Add or update tests covering at least:
- slot-finding service success case
- missing required info case(s)
- no-availability case
- invalid service/location/date case
- multi-turn continuity for persisted booking context if implemented in this PR
- tenant-safe behavior where relevant

### Documentation requirements
Update docs so engineering and product can understand:
- how slot-finding works
- what context is required
- what is persisted between turns
- what the assistant returns in success vs follow-up vs no-slots scenarios

### Deliverable format
Please:
- create a focused branch for this PR
- implement the code changes
- add/adjust tests
- update docs
- provide a concise summary of changed files, architecture decisions, tradeoffs, and follow-up risks

---

# PR 2 — Handoff MVP vertical slice

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to implement a **thin but real handoff-to-human MVP** for the assistant.

### Product goal
When a user says they want to talk to a human attendant, the assistant should:
- recognize the handoff request
- create a real persistent handoff record
- also create an operational CRM interaction/timeline entry
- return a clear user-facing confirmation
- make the handoff discoverable internally via a minimal visibility path

### Critical constraints
- **Do not build a full queueing/SLA system.** This is an MVP.
- **Do not wait for the full future handoff domain design.** Create the minimum durable version now.
- **Reuse existing CRM interaction capabilities** for operational visibility.
- **Keep multitenancy strict.** All handoff records and lookups must be tenant-scoped.
- **Be robust** against duplicate creation, missing customer context, and repeated handoff intent in the same conversation.

### Existing repo context you must inspect and reuse
Please inspect these areas before coding:
- chatbot normalized response and handoff-related fields
- assistant/chatbot route layer
- CRM interaction creation path
- tenant enforcement and auth dependencies
- any current assistant/session persistence

At minimum, inspect files equivalent to:
- `modules/chatbot/service/normalizer.py`
- `app/http/routes/chatbot.py`
- `modules/crm/service/crm_service.py`
- current CRM interaction model/repo/service flow
- docs under `docs/planning/*`

### Required deliverables
1. A **lightweight handoff persistence model**.
   - Introduce a new table/model/repo/service for assistant handoffs.
   - Keep fields minimal but useful, such as tenant, conversation, session, customer, status, reason, summary, created/updated timestamps.
2. A **handoff creation path** from assistant context.
   - This may be a dedicated assistant/handoff route or a safe extension of current assistant flow.
3. A **CRM interaction side effect** on handoff creation.
   - Suggested interaction type: `assistant_handoff`.
4. A **minimal internal visibility mechanism**.
   - Example: list open handoffs for staff users via API, with optional thin UI if cheap.
5. Tests and docs.

### Functional expectations
Support at least the following cases:
- Explicit user request for human assistance creates one handoff.
- Repeated request in the same active conversation should not create uncontrolled duplicates.
- Missing customer context should still create a usable handoff record when possible, but clearly mark missing fields.
- Staff can list or inspect open handoffs in MVP form.

### Suggested implementation shape
You may refine after inspecting the repo, but the intended shape is:
- new assistant handoff ORM + Alembic migration
- new repo/service under `modules/assistant/*`
- route integration in the assistant/chatbot layer
- CRM interaction write on handoff creation
- minimal API path for internal visibility

### Robustness requirements
- Ensure idempotent-ish behavior for repeated handoff requests in the same unresolved conversation.
- Keep statuses simple, e.g. `open`, `claimed`, `closed`.
- Preserve tenant scoping in every query.
- Keep user-facing responses stable and human-readable.
- Do not create side effects before validating tenant/auth context.
- If customer is unknown, still persist the handoff with clear metadata rather than failing hard unless the current architecture makes that unsafe.

### Testing requirements
Add or update tests covering at least:
- handoff creation success
- repeated handoff intent / duplicate prevention behavior
- CRM interaction is written on handoff creation
- list open handoffs
- tenant isolation for handoff reads/writes
- permission/auth behavior for internal visibility route(s)

### Documentation requirements
Update docs so engineering and operations understand:
- what a handoff record is in MVP form
- which assistant phrases/conditions trigger it
- what status model is supported
- how internal staff can discover pending handoffs
- what is intentionally deferred to later iterations

### Deliverable format
Please:
- create a focused branch for this PR
- implement the model, migration, repo/service, route integration, tests, and docs
- summarize decisions, assumptions, and follow-up improvements for a fuller handoff system

---

# PR 3 — Persistence and conversation continuity

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to add **lightweight assistant persistence for intent, state, and recent history**, so that booking and handoff flows can continue coherently across turns.

### Product goal
The assistant should remember enough from recent conversation context to:
- continue slot-finding without asking for the same thing twice
- remember that a handoff is already in progress
- support basic debugging/support visibility for assistant interactions

### Critical constraints
- **Do not build a full chat platform.** Keep persistence intentionally lightweight.
- **Do not store excessive or redundant history** if a compact state model will do.
- **Preserve multitenancy** and existing session model.
- **Be robust** around partial state, missing session IDs, conversation resets, and stale data.

### Existing repo context you must inspect and reuse
Please inspect these areas before coding:
- current `chatbot_conversation_sessions` ORM and repo
- assistant/chatbot route flow
- any planning docs for intent/history persistence
- current reset semantics

At minimum, inspect files equivalent to:
- `modules/chatbot/models/conversation_session_orm.py`
- `modules/chatbot/repo/session_repo.py`
- `app/http/routes/chatbot.py`
- `modules/chatbot/service/normalizer.py`
- docs under `docs/planning/*`

### Required deliverables
1. Extend session persistence with **latest intent and compact state/context**.
   - Suggested additions: `last_intent`, optional confidence, `state_payload` / `context_payload`.
2. Add **lightweight message history persistence** for assistant turns.
   - Store enough to reconstruct recent user and assistant turns.
   - Keep the schema small and operationally useful.
3. Load and use persisted state/history during follow-up turns.
   - Booking flow continuity
   - Handoff continuity
4. Tests and docs.

### Functional expectations
Support at least the following cases:
- User asks for booking help, provides missing info in a later turn, and the assistant continues from prior context.
- User asks for human help and the assistant remembers the handoff is already requested/in progress.
- Conversation reset clears or invalidates state appropriately.
- Persisted history is enough to inspect recent assistant behavior for support/debugging.

### Suggested implementation shape
You may refine after inspecting the repo, but the intended shape is:
- extend current conversation session schema via migration
- add a new assistant/chatbot message history table
- add repo methods for append/list/update state
- update assistant/chatbot route/service flow to read/write state/history on every turn

### Robustness requirements
- Keep history storage compact and predictable.
- Avoid storing sensitive or unnecessary raw payloads unless already aligned with repo patterns.
- Be careful with resets so stale state does not bleed into future turns.
- Never allow cross-tenant conversation/history access.
- Use clear fallback behavior when state is missing or partially corrupted.

### Testing requirements
Add or update tests covering at least:
- persist latest intent/state
- append and read message history
- multi-turn booking continuity
- multi-turn handoff continuity / duplicate suppression signal
- reset behavior
- tenant isolation for state/history

### Documentation requirements
Update docs so engineering understands:
- what is persisted in session state
- what is persisted as message history
- how state is loaded on new turns
- how reset affects stored continuity data

### Deliverable format
Please:
- create a focused branch for this PR
- implement migrations, models, repo changes, route/service updates, tests, and docs
- summarize schema choices, retention assumptions, and future scalability considerations

---

# PR 4 — E2E and final polish

## Codex prompt

You are working in the repository `viniciusandrade95/theone`.

Your task is to add **end-to-end coverage and final integration polish** for the assistant quick wins increment.

### Product goal
By the end of this PR, the repo should prove—through realistic end-to-end tests—that the assistant can:
1. suggest real appointment slots when the user asks for a time
2. create a real handoff when the user asks to talk to an attendant

This PR should also fix small bugs or UX/API inconsistencies discovered while integrating the previous slices.

### Critical constraints
- **The E2E tests must validate real backend side effects**, not only assistant text.
- **Do not mock away the product behavior completely.** Keep the test meaningful.
- **Do not introduce brittle tests** that depend on unstable timestamps or random data without control.
- **Preserve multitenancy and current test conventions.**

### Existing repo context you must inspect and reuse
Please inspect these areas before coding:
- current assistant frontend page (if UI-based E2E is practical)
- existing API tests for chatbot and assistant prebook
- any current E2E/test tooling already in the repository
- slot-finding and handoff implementations from the previous PRs

At minimum, inspect files equivalent to:
- `frontend/app/dashboard/assistant/page.tsx`
- `tests/api/test_chatbot_api.py`
- `tests/api/test_assistant_prebook.py`
- any existing frontend testing or browser automation config

### Required deliverables
1. Add an E2E test for the flow: **user asked for a time slot**.
2. Add an E2E test for the flow: **I want to talk to an attendant**.
3. Apply any needed polish/fixes uncovered by integrated testing.
4. Update docs if the final behavior differs from the earlier plan.

### Flow 1 expectations: user asked for a time slot
The test should demonstrate that:
- the assistant receives a booking-related request
- enough context is resolved directly or through follow-up turns
- the assistant returns real slots from the actual booking source of truth
- conversation continuity/state is persisted

### Flow 2 expectations: I want to talk to an attendant
The test should demonstrate that:
- the assistant receives a handoff request
- a real handoff record is created
- a CRM interaction is created
- the assistant returns a clear confirmation
- the internal visibility path can discover the pending handoff

### Testing guidance
Choose the strongest practical E2E style available in the repo:
- API-driven end-to-end if that is the current project norm
- UI/browser E2E only if the repo already has or can cheaply support it

If no browser E2E framework exists, prefer **robust API-driven end-to-end tests** over introducing a heavy new stack just for this PR.

### Robustness requirements
- Seed deterministic tenants/services/locations/booking settings/data.
- Control time/date assumptions carefully.
- Avoid flaky assertions on unordered slot lists unless ordering is guaranteed.
- Assert backend artifacts, not just response strings.
- Keep assistant/frontend polish small and targeted.

### Testing requirements
At minimum, your test suite for this PR must assert:
- real slot suggestions are returned for a seeded scenario
- no-slot or missing-info paths remain stable if touched
- handoff record exists after handoff flow
- CRM interaction exists after handoff flow
- internal pending handoff visibility works
- tenant isolation is preserved in the tested flows

### Documentation requirements
Update docs with:
- how to run the E2E tests
- what each E2E flow validates
- any setup/seed requirements

### Deliverable format
Please:
- create a focused branch for this PR
- add the E2E tests and minimal required polish
- summarize what was tested end-to-end, what remains uncovered, and any known limitations

---

## Optional extra instruction for all PR prompts

If you want a single reusable tail to append to every Codex prompt, use this:

> Before changing code, inspect the existing implementation and explain the current architecture relevant to this PR. Then implement the smallest robust change set that satisfies the product goal while preserving multitenancy, existing error conventions, and current route boundaries. Add tests for success paths, failure paths, and tenant-safety where relevant. Update docs. At the end, summarize changed files, migrations, tests added, tradeoffs, and follow-up risks.
