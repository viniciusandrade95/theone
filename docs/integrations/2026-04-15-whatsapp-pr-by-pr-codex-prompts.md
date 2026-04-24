# TheOne — Prompts de Codex para cada PR do plano WhatsApp

Data: 2026-04-15

Baseado em:
- `docs/integrations/2026-04-15-whatsapp-pr-by-pr-plan.md`
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`

## Como usar

Cada secção abaixo é um prompt pronto para colar no Codex.

Regras gerais já embutidas nos prompts:
- trabalhar dentro do repo `viniciusandrade95/theone`
- manter mudanças incrementais
- não copiar a implementação do `applandlord`
- aproveitar a arquitetura já existente do `theone`
- evitar refactors fora do scope da PR

---

# PR 1 — Setup, docs e validação ponta-a-ponta da integração Meta

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Harden and clarify the existing WhatsApp Meta integration setup so the team can configure, validate and test it end to end.

Important context:
- Do NOT copy applandlord implementation literally.
- TheOne already has a stronger architecture: inbound webhook, HMAC verification, tenant routing, provider-backed outbound, deeplink fallback, history and delivery lifecycle.
- This PR should consolidate and document what already exists.

Scope strictly limited to:
- .env.example
- docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md
- docs/features/outbound-basic-mvp.md
- app/http/routes/messaging.py
- modules/messaging/providers/meta_whatsapp_cloud.py
- modules/messaging/providers/meta_cloud.py
- tests/api/test_inbound_webhook.py
- tests/api/test_outbound_provider_lifecycle_api.py

Tasks:
1. Review and normalize the WhatsApp-related environment variables in .env.example:
   - WHATSAPP_WEBHOOK_SECRET
   - WHATSAPP_WEBHOOK_VERIFY_TOKEN
   - WHATSAPP_CLOUD_ACCESS_TOKEN
   - WHATSAPP_CLOUD_API_VERSION
   - WHATSAPP_CLOUD_TIMEOUT_SECONDS
2. Improve docs so a developer/operator can understand:
   - GET webhook verification flow
   - POST inbound webhook flow
   - provider-backed outbound flow
   - fallback wa.me flow
   - delivery callback flow
3. Review current messaging/provider files for clarity and small fixes only if needed.
4. Add or improve tests for the minimum viable end-to-end validation path.
5. Add an operational checklist to docs for manual verification.

Constraints:
- Keep changes incremental.
- Do not redesign product UI in this PR.
- Do not introduce new architecture unless absolutely necessary.
- Do not rename env vars unless there is a strong reason; prefer consistency with existing TheOne conventions.

Deliverables:
- clearer setup docs
- consistent env var docs
- tests updated
- minimal code clarifications only where needed
```

---

# PR 2 — Melhorar a página admin de ligação WhatsApp

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Turn the WhatsApp admin account page from a technical raw form into a clearer product/admin connection experience.

Important context:
- TheOne resolves tenant routing by provider + phone_number_id.
- This is good and should remain.
- The goal is to improve usability and product framing, not to rebuild backend architecture.

Scope strictly limited to:
- frontend/app/dashboard/admin/whatsapp-accounts/page.tsx
- app/http/routes/messaging.py
- docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md

Tasks:
1. Improve the page framing so it feels like “Connect WhatsApp number” instead of a raw technical form.
2. Explain what Meta phone_number_id is in simple language.
3. Make provider, status and success/error states clearer.
4. Prepare the UI to communicate product-facing connection concepts such as:
   - connection status
   - webhook verification status
   - last delivery callback received
5. Preserve compatibility with the current backend endpoint for whatsapp account creation.
6. Update docs if the UI wording or expected workflow changes.

Constraints:
- Keep current backend flow working.
- Do not redesign all messaging pages.
- Avoid overengineering.
- Focus on product/admin clarity.

Deliverables:
- improved WhatsApp admin connection page
- cleaner admin UX copy
- docs aligned if needed
```

---

# PR 3 — Validar e productizar outbound send simples

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Make the current outbound send flow more understandable and product-ready, while keeping the existing provider-backed + fallback architecture.

Important context:
- In applandlord, there was a simple helper lib/whatsapp.ts.
- In TheOne, the conceptual equivalent already exists in modules/messaging/providers/meta_whatsapp_cloud.py and app/http/routes/outbound.py.
- The task is not to simplify architecture, but to make the existing flow clearer and stronger.

Scope strictly limited to:
- app/http/routes/outbound.py
- modules/messaging/providers/meta_whatsapp_cloud.py
- docs/features/outbound-basic-mvp.md
- tests/api/test_outbound_provider_lifecycle_api.py

Tasks:
1. Review the outbound send flow and make sure the result is easy to understand from the API response.
2. Clarify behavior for:
   - provider-backed send success
   - fallback deeplink case
   - send failure
3. Review notes/messages returned to the UI so they are clearer.
4. Review idempotency and duplicate send behavior for readability and correctness.
5. Improve docs so the meaning of states is explicit:
   - sent
   - accepted
   - failed
   - unconfirmed
6. Keep historical recording and provider_message_id behavior coherent.

Constraints:
- Do not replace TheOne’s flow with a simplistic helper-only model.
- Do not redesign unrelated messaging features.
- Keep changes incremental and easy to review.

Deliverables:
- clearer outbound send behavior
- improved docs
- updated lifecycle tests where needed
```

---

# PR 4 — Templates default e casos de uso equivalentes ao applandlord

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Cover the useful applandlord-style WhatsApp business use cases in the proper TheOne product architecture.

Important context:
- Do NOT create hacky isolated routes just because applandlord had simple route.ts files.
- Prefer TheOne’s existing outbound/templates/domain approach.
- Focus on product use cases: reminders, booking confirmations, reactivation, summary/reporting.

Scope primarily limited to:
- app/http/routes/outbound.py
- frontend/app/dashboard/outbound/templates/... (only if the repo structure already supports it or needs minimal additions)
- docs/features/outbound-basic-mvp.md
- docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md
- tests/api/test_outbound_provider_lifecycle_api.py

Tasks:
1. Ensure default useful template types exist or are properly documented and usable:
   - booking_confirmation
   - reminder_24h
   - reminder_3h
   - reactivation
2. Model applandlord-like use cases using TheOne outbound infra rather than isolated one-off endpoints.
3. Define how a business summary/report action should fit the product, even if only partially implemented in this PR.
4. Update docs to explain how these cases replace applandlord’s “send reminder” and “send report” approach.
5. Keep the solution tenant-aware and consistent with current architecture.

Constraints:
- No copy-paste implementation from applandlord.
- No architecture downgrade.
- Keep everything product/domain aligned.

Deliverables:
- stronger default outbound use-case support
- clearer docs
- incremental code changes only
```

---

# PR 5 — Surface de delivery lifecycle na UI

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Surface WhatsApp delivery lifecycle states in the right UI places so the product communicates real value.

Important context:
- TheOne already has lifecycle concepts beyond applandlord.
- The UI should make it clear whether a message was merely initiated, accepted by provider, delivered, read or failed.
- Do not confuse legacy status with delivery_status.

Scope primarily limited to:
- frontend/app/dashboard/customers/... (where outbound/customer history lives, use existing structure)
- frontend/app/dashboard/page.tsx
- app/http/routes/outbound.py
- docs/features/outbound-basic-mvp.md

Tasks:
1. Identify the right UI surfaces for delivery state:
   - customer message/history context
   - dashboard home if relevant
   - outbound history if already present
2. Make state labels understandable:
   - accepted
   - delivered
   - read
   - failed
   - unconfirmed
3. Improve backend-to-UI mapping if needed so delivery state is easy to consume.
4. Update docs to explain meaning and product value of these states.

Constraints:
- Do not create a full chat product in this PR.
- Keep the changes focused on delivery state visibility.
- Preserve backward compatibility where possible.

Deliverables:
- clearer delivery state UI
- cleaner state semantics in docs/code
```

---

# PR 6 — Inbox summary e pending replies

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Close the communication loop by surfacing pending replies and unread conversation summary.

Important context:
- Sending is not enough; the product must show what still needs a reply.
- The dashboard/home should gain communication visibility.
- Full inbox complexity is not required if a solid summary can be delivered first.

Scope primarily limited to:
- app/http/routes/dashboard.py
- app/http/routes/messaging.py
- frontend/app/dashboard/page.tsx
- frontend/components/dashboard/PendingInboxCard.tsx
- frontend/app/dashboard/inbox/page.tsx (if needed)
- frontend/lib/contracts/inbox.ts (if needed)

Tasks:
1. Define “awaiting reply” conservatively and explicitly.
2. Add backend summary support for:
   - unread conversations count
   - awaiting reply count
   - optionally latest inbound summary if easy to support
3. Surface that summary in the dashboard home.
4. Create or improve a minimal inbox entry point if helpful.
5. Keep docs and naming aligned with the broader dashboard roadmap.

Constraints:
- Do not attempt a full WhatsApp inbox product if the current architecture is not ready.
- Prefer an honest incremental summary.
- Avoid unrelated messaging rewrites.

Deliverables:
- dashboard pending communication summary
- optional minimal inbox entry point
- aligned contracts/docs
```

---

# PR 7 — Botões e ações rápidas de WhatsApp no CRM

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Bring WhatsApp closer to day-to-day CRM operations through quick actions in the right places.

Important context:
- Users should not need to dig through technical flows or template screens for every simple WhatsApp action.
- Reuse the existing outbound/template infrastructure.

Scope primarily limited to:
- frontend/app/dashboard/customers/...
- frontend/app/dashboard/appointments/...
- frontend/app/dashboard/page.tsx
- app/http/routes/outbound.py

Tasks:
1. Add a simple “Send WhatsApp” action in appropriate CRM surfaces.
2. Add quick shortcuts where it makes sense for:
   - reminder
   - booking confirmation
   - follow-up / reactivation if already supported
3. Reuse existing outbound/template flow instead of creating duplicate send logic.
4. Keep the UX simple and product-oriented.

Constraints:
- Do not create multiple competing send flows.
- Do not rebuild the CRM.
- Prefer minimal high-value quick actions.

Deliverables:
- WhatsApp quick actions in the CRM
- reuse of existing outbound infra
- focused incremental UI improvements
```

---

# PR 8 — Report diário/semanal por WhatsApp como feature de produto

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Implement the clean TheOne version of applandlord’s WhatsApp report sending feature.

Important context:
- Applandlord had a simple app/api/reports/whatsapp/route.ts.
- In TheOne, this should become a product/domain feature using existing outbound infrastructure and tenant-aware metrics.
- Avoid hacks.

Scope primarily limited to:
- app/http/routes/outbound.py or a small dedicated reporting/outbound route area if clearly justified
- app/http/routes/dashboard.py
- reporting/analytics-related modules if needed
- docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md
- relevant tests

Tasks:
1. Define a business summary/report action for WhatsApp.
2. Calculate sensible tenant-level metrics for that report.
3. Send the report to an admin/business phone configured through product settings.
4. Keep the implementation aligned with existing outbound infrastructure.
5. Document manual use now and future automation possibilities.

Constraints:
- Do not create a random isolated endpoint if it can fit cleanly in the current product model.
- Keep it tenant-aware.
- Keep it reviewable and incremental.

Deliverables:
- report-by-WhatsApp feature aligned with TheOne architecture
- updated docs
- tests where relevant
```

---

# PR 9 — Endurecimento técnico antes de escalar WhatsApp

```text
You are working inside repo viniciusandrade95/theone.

Goal:
Address the most important technical risks that could make WhatsApp unreliable or unsafe in production.

Important context:
- TheOne’s own technical audit already points to key WhatsApp-related risks:
  - secrets in repo
  - billing in-memory inconsistency
  - RLS vs inbound tenant lookup
  - lack of RBAC
  - lack of observability
- This PR is about hardening, not product polish.

Scope primarily limited to the areas truly required by the audit findings, such as:
- docs/audit/2026-04-09-technical-audit.md
- app/http/routes/messaging.py
- modules/messaging/repo/sql.py
- core/observability/...
- app/http/routes/billing.py
- RBAC/tenancy-related files as needed

Tasks:
1. Review and reduce the highest-risk items affecting WhatsApp operations.
2. Improve inbound tenant lookup safety and reliability where needed.
3. Add minimum viable observability for inbound/outbound/delivery flow.
4. Add minimum RBAC protections for sensitive admin flows if in scope.
5. Keep the work tightly aligned to the audit findings and document what was addressed.

Constraints:
- Do not attempt a giant platform rewrite.
- Prioritize the highest risk issues first.
- Keep changes reviewable and explicit.
- Be honest in docs about what remains unresolved.

Deliverables:
- improved technical footing for WhatsApp in production
- docs updated against audit reality
- focused hardening changes only
```

---

## Ordem recomendada de execução

1. PR 1 — Setup, docs e validação ponta-a-ponta da integração Meta
2. PR 2 — Melhorar a página admin de ligação WhatsApp
3. PR 3 — Validar e productizar outbound send simples
4. PR 4 — Templates default e casos de uso equivalentes ao applandlord
5. PR 5 — Surface de delivery lifecycle na UI
6. PR 6 — Inbox summary e pending replies
7. PR 7 — Botões e ações rápidas de WhatsApp no CRM
8. PR 8 — Report diário/semanal por WhatsApp como feature de produto
9. PR 9 — Endurecimento técnico antes de escalar WhatsApp

---

## Ordem mínima para ganhar velocidade

Se quiseres avançar já no essencial:
1. PR 1
2. PR 2
3. PR 3
4. PR 5
5. PR 6

Isso já torna o WhatsApp muito mais utilizável e visível no `theone`.
