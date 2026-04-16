# TheOne — Checklist PR por PR + Prompts para Codex

Data: 2026-04-15

## Como usar

Este documento divide o plano em PRs pequenas e revisáveis.

Cada PR tem:
- objetivo
- scope
- ficheiros principais
- checklist
- critérios de aceitação
- prompt pronto para colar no Codex

### Regra geral para todas as PRs
- não mexer em ficheiros fora do scope sem necessidade real;
- manter compatibilidade com o que já existe;
- preservar naming e convenções do repo;
- atualizar testes afetados;
- não reescrever a arquitetura toda numa PR só.

---

# PR 1 — Dashboard metrics contract + backend foundation

## Objetivo
Preparar a fundação da nova home mobile-first no backend e no contrato TS, sem ainda refazer a UI inteira.

## Scope
- expandir `/dashboard/overview`
- alinhar tipos TS
- documentar métricas novas
- adicionar testes mínimos

## Ficheiros principais
- `app/http/routes/dashboard.py`
- `frontend/lib/contracts/dashboard.ts`
- `tests/api/test_dashboard_overview_api.py`
- `docs/features/operational-dashboard-mvp.md`
- `docs/product/dashboard-metrics-glossary.md` (novo)
- `docs/product/home-v1-information-architecture.md` (novo)

## Checklist
- [ ] definir `revenue_today`
- [ ] definir `revenue_month`
- [ ] definir `revenue_today_delta_pct`
- [ ] definir `revenue_month_delta_pct`
- [ ] definir `pending_messages_count` como campo reservado, mesmo que inicialmente devolva `0`
- [ ] definir `next_appointments`
- [ ] manter compatibilidade com campos já usados pela home atual
- [ ] atualizar contrato TS
- [ ] adicionar/atualizar testes API
- [ ] documentar limitações do cálculo de revenue v1

## Critérios de aceitação
- endpoint continua funcional
- frontend consegue compilar com o contrato novo
- revenue v1 usa appointments concluídos
- testes do dashboard passam

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: implement the backend/data-contract foundation for the new mobile-first dashboard home.

Scope strictly limited to:
- app/http/routes/dashboard.py
- frontend/lib/contracts/dashboard.ts
- tests/api/test_dashboard_overview_api.py
- docs/features/operational-dashboard-mvp.md
- create docs/product/dashboard-metrics-glossary.md
- create docs/product/home-v1-information-architecture.md

Requirements:
1. Expand the dashboard overview response shape with:
   - revenue_today
   - revenue_month
   - revenue_today_delta_pct
   - revenue_month_delta_pct
   - pending_messages_count
   - next_appointments
2. Revenue v1 must be derived from completed appointments only.
3. Keep backward compatibility with existing overview fields already used by the current frontend.
4. If pending messages are not fully implemented yet, return a safe placeholder value and document it honestly.
5. Update TypeScript dashboard contracts accordingly.
6. Update/add API tests for the new response shape.
7. Keep the implementation simple and consistent with current repo style.
8. Do not redesign the frontend home in this PR.

Implementation notes:
- Prefer incremental changes.
- Add concise comments only where logic is non-obvious.
- Preserve timezone-aware calculations already present in dashboard.py.
- Avoid unrelated refactors.

Deliverables:
- code changes
- tests updated
- docs updated
```

---

# PR 2 — Dashboard shell, TopBar and mobile nav cleanup

## Objetivo
Melhorar a shell da app para parecer mobile-first e mais premium, sem ainda mexer pesado na home.

## Scope
- top bar
- mobile nav
- layout shell
- espaço visual para data/contexto e hide revenue

## Ficheiros principais
- `frontend/components/dashboard/TopBar.tsx`
- `frontend/components/dashboard/MobileNav.tsx`
- `frontend/components/dashboard/SidebarNav.tsx`
- `frontend/components/dashboard/DashboardLayout.tsx`
- `frontend/app/dashboard/layout.tsx`
- `frontend/lib/default-location.tsx`

## Checklist
- [ ] destacar a data atual no top bar
- [ ] mostrar contexto operacional mais claro
- [ ] rever ordem dos itens mobile nav
- [ ] tornar Home/Calendar/Customers/Messages mais prioritários
- [ ] reduzir ruído técnico visível
- [ ] garantir que layout continua responsivo
- [ ] não partir auth/layout providers existentes

## Critérios de aceitação
- top bar fica visualmente mais forte
- mobile nav parece mais orientada a produto
- layout continua funcional em mobile e desktop

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: improve the dashboard shell so it feels mobile-first and more product-oriented.

Scope strictly limited to:
- frontend/components/dashboard/TopBar.tsx
- frontend/components/dashboard/MobileNav.tsx
- frontend/components/dashboard/SidebarNav.tsx
- frontend/components/dashboard/DashboardLayout.tsx
- frontend/app/dashboard/layout.tsx
- frontend/lib/default-location.tsx

Requirements:
1. Make the TopBar show the current date in a clearer, more product-centered way.
2. Reduce technical noise in the top shell.
3. Reorder mobile navigation to better reflect product priorities:
   - Home/Overview
   - Calendar
   - Customers
   - Messages/Outbound if applicable
4. Keep desktop sidebar functional.
5. Preserve RequireAuth and DefaultLocationProvider flows.
6. Keep code consistent with the current component style.
7. Do not redesign the dashboard home page in this PR.

Implementation notes:
- Prefer minimal but meaningful UI structure improvements.
- Do not introduce heavy dependencies.
- Keep behavior stable.
- If needed, expose default location info in a way that can be reused later by the dashboard home.

Deliverables:
- updated shell components
- improved mobile nav priority
- no unrelated refactors
```

---

# PR 3 — Shared dashboard home components

## Objetivo
Criar a base reutilizável da nova home antes de reescrever `/dashboard`.

## Scope
- componentes base de cards e secções

## Ficheiros principais
- `frontend/components/dashboard/KpiCard.tsx` (novo)
- `frontend/components/dashboard/MoneyCard.tsx` (novo)
- `frontend/components/dashboard/QuickActionsGrid.tsx` (novo)
- `frontend/components/dashboard/SectionHeader.tsx` (novo)
- `frontend/components/dashboard/TodayAppointmentsList.tsx` (novo)
- `frontend/components/dashboard/PendingInboxCard.tsx` (novo)
- `frontend/components/dashboard/TrendMiniCard.tsx` (novo)

## Checklist
- [ ] criar `KpiCard`
- [ ] criar `MoneyCard` com hidden state
- [ ] criar `QuickActionsGrid`
- [ ] criar `SectionHeader`
- [ ] criar `TodayAppointmentsList`
- [ ] criar `PendingInboxCard`
- [ ] criar `TrendMiniCard`
- [ ] manter componentes pequenos e composable

## Critérios de aceitação
- os componentes compõem a nova home sem lógica duplicada
- a UI é consistente entre cards
- não há dependência circular nem acoplamento desnecessário

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: create reusable dashboard home components before the page rewrite.

Scope strictly limited to creating/updating dashboard presentation components:
- frontend/components/dashboard/KpiCard.tsx
- frontend/components/dashboard/MoneyCard.tsx
- frontend/components/dashboard/QuickActionsGrid.tsx
- frontend/components/dashboard/SectionHeader.tsx
- frontend/components/dashboard/TodayAppointmentsList.tsx
- frontend/components/dashboard/PendingInboxCard.tsx
- frontend/components/dashboard/TrendMiniCard.tsx

Requirements:
1. Build small reusable components for the new dashboard home.
2. MoneyCard must support a hidden/masked money state.
3. KpiCard should support label, value, optional hint, optional trend.
4. TodayAppointmentsList should be compact and ready to render upcoming appointments.
5. PendingInboxCard should support counts and quick links, even if initially fed by placeholder data.
6. Keep styling aligned with the existing dashboard UI language.
7. Do not rewrite frontend/app/dashboard/page.tsx in this PR.

Implementation notes:
- Prefer clear props and low coupling.
- Keep files focused.
- No extra libraries.

Deliverables:
- reusable components ready for use in the dashboard home rewrite
```

---

# PR 4 — New mobile-first dashboard home

## Objetivo
Refazer `/dashboard` para ficar alinhada com a visão mobile-first.

## Scope
- nova organização da home
- revenue cards
- booking snapshot
- quick actions certas
- próximos appointments
- pending inbox placeholder/real if available

## Ficheiros principais
- `frontend/app/dashboard/page.tsx`
- `frontend/lib/contracts/dashboard.ts`
- componentes criados na PR 3

## Checklist
- [ ] reorganizar a home em blocos claros
- [ ] mostrar `revenue_today` e `revenue_month`
- [ ] mostrar booking snapshot
- [ ] mostrar quick actions prioritárias
- [ ] mostrar próximos appointments
- [ ] mostrar pending messages card
- [ ] suportar loading/error/empty states bons
- [ ] manter comportamento desktop aceitável, mesmo antes da PR desktop

## Critérios de aceitação
- a home já parece cockpit diário
- os dados principais aparecem acima
- a leitura em mobile é muito mais clara

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: rewrite frontend/app/dashboard/page.tsx into a mobile-first operational home.

Scope strictly limited to:
- frontend/app/dashboard/page.tsx
- frontend/lib/contracts/dashboard.ts (only if minor alignment is still needed)
- usage of dashboard components created previously

Requirements:
1. Reorganize the dashboard home into clear sections:
   - contextual header
   - revenue today / revenue month
   - booking snapshot
   - quick actions
   - next appointments
   - pending communication
   - opportunity/trend section
2. Prioritize mobile readability and 5-second scanability.
3. Use reusable dashboard components instead of large inline UI blocks.
4. Preserve loading, error and empty states.
5. Keep the page compatible with the current API contract.
6. Do not redesign unrelated dashboard pages in this PR.

Implementation notes:
- Mobile first, then progressively enhance larger breakpoints.
- Keep the code cleaner than the current inline-heavy structure.
- Avoid overengineering.

Deliverables:
- rewritten dashboard page
- improved section hierarchy
- no unrelated refactors
```

---

# PR 5 — Login aesthetic redesign

## Objetivo
Melhorar muito a percepção do produto na página de login sem partir a lógica atual.

## Scope
- melhorar UI/UX do login
- melhorar workspace selection step

## Ficheiros principais
- `frontend/app/login/page.tsx`
- `frontend/components/ui/card.tsx` (só se necessário)
- `frontend/components/ui/input.tsx` (só se necessário)
- `frontend/lib/auth.ts` (só se houver ajuste pequeno de UX)

## Checklist
- [ ] headline mais forte
- [ ] subtítulo melhor
- [ ] layout mais premium
- [ ] estados de erro melhores
- [ ] loading mais elegante
- [ ] workspace step mais claro
- [ ] sem mudar a lógica de auth desnecessariamente

## Critérios de aceitação
- login continua a funcionar
- visual parece claramente melhor
- seleção de workspace fica mais compreensível

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: redesign the login page UI/UX to feel more premium while keeping the current auth logic intact.

Scope strictly limited to:
- frontend/app/login/page.tsx
- optionally frontend/components/ui/card.tsx
- optionally frontend/components/ui/input.tsx
- optionally frontend/lib/auth.ts for very small UX-related adjustments only

Requirements:
1. Improve visual hierarchy, spacing, copy and overall polish.
2. Keep the existing email/password + workspace selection flow intact.
3. Make the workspace selection step clearer and more elegant.
4. Preserve all functional behavior.
5. Do not introduce unrelated routing/auth changes.

Implementation notes:
- Keep the page simple, calm, premium and readable.
- Prioritize mobile and tablet behavior.
- Avoid flashy styling.

Deliverables:
- redesigned login page
- no auth regression
```

---

# PR 6 — Register redesign + onboarding skeleton

## Objetivo
Transformar o register numa entrada para onboarding real.

## Scope
- melhorar register
- criar onboarding visual mínimo
- sem ainda persistir tudo

## Ficheiros principais
- `frontend/app/register/page.tsx`
- `frontend/app/onboarding/page.tsx` (novo)
- `frontend/components/onboarding/OnboardingStepper.tsx` (novo)
- `frontend/components/onboarding/BusinessProfileStep.tsx` (novo)
- `frontend/components/onboarding/HowYouWorkStep.tsx` (novo)
- `frontend/components/onboarding/HomePrioritiesStep.tsx` (novo)
- `frontend/components/onboarding/ChannelsStep.tsx` (novo)
- `frontend/components/onboarding/FinishStep.tsx` (novo)

## Checklist
- [ ] register mais bonito e claro
- [ ] onboarding route criada
- [ ] stepper funcional
- [ ] steps essenciais montados
- [ ] sem persistência final complexa ainda
- [ ] fluxo de navegação claro

## Critérios de aceitação
- o onboarding já existe e pode ser demonstrado
- register deixa de parecer fluxo terminal

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: redesign register and create an onboarding UI skeleton.

Scope strictly limited to:
- frontend/app/register/page.tsx
- frontend/app/onboarding/page.tsx
- frontend/components/onboarding/OnboardingStepper.tsx
- frontend/components/onboarding/BusinessProfileStep.tsx
- frontend/components/onboarding/HowYouWorkStep.tsx
- frontend/components/onboarding/HomePrioritiesStep.tsx
- frontend/components/onboarding/ChannelsStep.tsx
- frontend/components/onboarding/FinishStep.tsx

Requirements:
1. Improve register page UI/UX.
2. Treat register as the entry into onboarding, not the whole journey.
3. Create a multi-step onboarding UI with only essential business/product questions.
4. Navigation between steps should work cleanly.
5. Persistence can be placeholder/local for now if needed; do not build the full backend in this PR.
6. Keep the implementation clean and demo-ready.

Implementation notes:
- Focus on structure, hierarchy and flow.
- Do not overcomplicate with a full form engine.
- Keep components reusable.

Deliverables:
- redesigned register page
- onboarding route and step components
```

---

# PR 7 — Onboarding persistence + preferences/settings

## Objetivo
Guardar preferências do onboarding para personalizar a home e o produto.

## Scope
- storage de preferências
- leitura/escrita de settings
- ligação onboarding -> backend

## Ficheiros principais
- `app/http/routes/auth.py`
- `app/http/routes/crm.py` ou rota de settings equivalente
- `modules/tenants/models/tenant_settings_orm.py`
- `modules/tenants/repo/settings_sql.py`
- `frontend/app/onboarding/page.tsx`
- `frontend/lib/contracts/settings.ts`
- migration Alembic se necessária

## Checklist
- [ ] decidir storage oficial
- [ ] adicionar campos necessários
- [ ] persistir preferências do onboarding
- [ ] devolver esses valores ao frontend
- [ ] garantir defaults seguros
- [ ] documentar os novos campos

## Critérios de aceitação
- onboarding grava informação real
- settings podem ser reutilizadas pela home

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: persist onboarding choices into settings/preferences that the dashboard can later consume.

Scope primarily limited to:
- app/http/routes/auth.py
- app/http/routes/crm.py or the existing settings route area
- modules/tenants/models/tenant_settings_orm.py
- modules/tenants/repo/settings_sql.py
- frontend/app/onboarding/page.tsx
- frontend/lib/contracts/settings.ts
- create Alembic migration if needed

Requirements:
1. Persist onboarding-derived preferences such as:
   - home_primary_focus
   - preferred_dashboard_layout
   - wants_whatsapp
   - wants_reminders
   - hide_revenue if this belongs in persisted settings
2. Use the repo’s existing settings patterns where possible.
3. Add safe defaults.
4. Wire frontend onboarding submission to backend persistence.
5. Keep the implementation incremental and understandable.
6. Do not redesign onboarding UI again in this PR.

Implementation notes:
- Prefer using existing tenant settings if that fits the current architecture.
- Add migration only if necessary.
- Keep API contracts explicit.

Deliverables:
- persisted onboarding preferences
- frontend connected to persistence
- migration if needed
```

---

# PR 8 — Pending messages / inbox summary on dashboard home

## Objetivo
Trazer mensagens por responder para a superfície principal da app.

## Scope
- resumo de pending messages no backend
- card na home
- eventual rota de inbox summary, se necessário

## Ficheiros principais
- `app/http/routes/dashboard.py`
- `app/http/routes/messaging.py`
- `app/http/routes/outbound.py`
- `frontend/app/dashboard/page.tsx`
- `frontend/components/dashboard/PendingInboxCard.tsx`
- `frontend/lib/contracts/inbox.ts` (novo, se necessário)
- `frontend/app/dashboard/inbox/page.tsx` (novo, se necessário)

## Checklist
- [ ] definir unread/awaiting reply
- [ ] expor summary simples para a home
- [ ] mostrar contagens e quick links
- [ ] ligar a customer/outbound/inbox quando possível
- [ ] documentar limitações se inbox completa ainda não existir

## Critérios de aceitação
- a home já mostra trabalho pendente comunicacional
- não é preciso abrir 3 páginas para perceber se há mensagens por responder

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: add pending communication visibility to the dashboard home.

Scope limited to:
- app/http/routes/dashboard.py
- app/http/routes/messaging.py
- app/http/routes/outbound.py
- frontend/app/dashboard/page.tsx
- frontend/components/dashboard/PendingInboxCard.tsx
- optionally frontend/lib/contracts/inbox.ts
- optionally frontend/app/dashboard/inbox/page.tsx if a minimal landing page is needed

Requirements:
1. Define and expose a simple summary for pending communication, such as:
   - unread conversations count
   - awaiting reply count
   - optional latest inbound summary if easy to support
2. Surface that summary in the dashboard home.
3. Keep the implementation honest if full inbox logic is not complete yet.
4. Prefer incremental backend additions instead of a full messaging rewrite.
5. Preserve existing messaging/outbound flows.

Implementation notes:
- Focus on summary visibility, not a full chat product.
- If exact inbox semantics are not fully available yet, return conservative/explicit values and document them.

Deliverables:
- backend summary
- dashboard home pending communication block
- optional minimal inbox entry page if helpful
```

---

# PR 9 — Desktop/tablet home composition with calendar preview

## Objetivo
Levar a home para layouts largos sem estragar a simplicidade mobile.

## Scope
- layout específico para `lg/xl`
- calendar preview / workspace composition
- right rail para pending messages/activity

## Ficheiros principais
- `frontend/app/dashboard/page.tsx`
- `frontend/app/dashboard/calendar/page.tsx`
- `frontend/components/dashboard/DesktopHomeLayout.tsx` (novo)
- `frontend/components/dashboard/HomeCalendarPreview.tsx` (novo)
- `frontend/components/dashboard/HomeRightRail.tsx` (novo)
- `frontend/components/dashboard/DashboardLayout.tsx`

## Checklist
- [ ] manter mobile clean
- [ ] criar composição desktop/tablet
- [ ] trazer calendário para a home em larguras maiores
- [ ] mover pending messages/opportunities para coluna lateral
- [ ] evitar duplicação excessiva com a página de calendar

## Critérios de aceitação
- home em desktop parece workspace, não só cards maiores
- mobile continua boa

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: create a larger-screen dashboard home composition with calendar presence while preserving mobile simplicity.

Scope limited to:
- frontend/app/dashboard/page.tsx
- frontend/app/dashboard/calendar/page.tsx
- frontend/components/dashboard/DesktopHomeLayout.tsx
- frontend/components/dashboard/HomeCalendarPreview.tsx
- frontend/components/dashboard/HomeRightRail.tsx
- frontend/components/dashboard/DashboardLayout.tsx

Requirements:
1. Keep mobile stacked and simple.
2. Add a more workspace-like layout for larger breakpoints.
3. Bring calendar presence into the dashboard home on tablet/desktop.
4. Use a right rail for pending communication/activity/opportunities when appropriate.
5. Reuse existing calendar concepts where possible.
6. Do not rebuild the full calendar page inside the home.

Implementation notes:
- Progressive enhancement by breakpoint.
- Keep composition clean and maintainable.
- Avoid giant conditional JSX blobs if possible.

Deliverables:
- improved large-screen home composition
- preserved mobile usability
```

---

# PR 10 — Trends, WhatsApp delivery state surface, QA and docs polish

## Objetivo
Fechar a sprint com sinais de negócio mais claros, status de entrega mais visíveis e documentação limpa.

## Scope
- trend cards melhores
- visibilidade de delivery states
- pequenos ajustes finais de docs/tests

## Ficheiros principais
- `frontend/app/dashboard/page.tsx`
- `frontend/app/dashboard/analytics/page.tsx`
- `frontend/components/dashboard/TrendMiniCard.tsx`
- `app/http/routes/outbound.py`
- `docs/features/operational-dashboard-mvp.md`
- `docs/product/home-v1-information-architecture.md`
- `tests/api/test_dashboard_overview_api.py`
- `tests/api/test_outbound_provider_lifecycle_api.py`

## Checklist
- [ ] mostrar trends curtas e explicáveis
- [ ] mostrar delivery states de WhatsApp mais visíveis na UI certa
- [ ] rever copy UX da home
- [ ] rever loading/empty/error states
- [ ] atualizar docs finais
- [ ] atualizar testes mais afetados

## Critérios de aceitação
- a home parece mais inteligente
- delivery states não ficam escondidos na infra
- docs e testes refletem a nova v1

## Prompt para Codex
```text
You are working inside repo viniciusandrade95/theone.

Goal: polish business trends, surface WhatsApp delivery states better, and finalize docs/tests.

Scope limited to:
- frontend/app/dashboard/page.tsx
- frontend/app/dashboard/analytics/page.tsx
- frontend/components/dashboard/TrendMiniCard.tsx
- app/http/routes/outbound.py
- docs/features/operational-dashboard-mvp.md
- docs/product/home-v1-information-architecture.md
- tests/api/test_dashboard_overview_api.py
- tests/api/test_outbound_provider_lifecycle_api.py

Requirements:
1. Improve trend presentation so it is short, concrete and understandable.
2. Surface WhatsApp delivery state more clearly where it adds product value.
3. Review UX copy and state handling for the dashboard.
4. Update docs to reflect the final v1 behavior.
5. Update affected tests.
6. Keep changes incremental and coherent with previous PRs.

Implementation notes:
- Avoid vague labels like “Trends” without context.
- Prefer explicit business meaning.
- Do not introduce large new features in this PR.

Deliverables:
- polished trend UI
- better delivery state visibility
- synced docs and tests
```

---

# Ordem recomendada de merge

1. PR 1 — Dashboard metrics contract + backend foundation
2. PR 2 — Dashboard shell, TopBar and mobile nav cleanup
3. PR 3 — Shared dashboard home components
4. PR 4 — New mobile-first dashboard home
5. PR 5 — Login aesthetic redesign
6. PR 6 — Register redesign + onboarding skeleton
7. PR 7 — Onboarding persistence + preferences/settings
8. PR 8 — Pending messages / inbox summary on dashboard home
9. PR 9 — Desktop/tablet home composition with calendar preview
10. PR 10 — Trends, WhatsApp delivery state surface, QA and docs polish

---

# Ordem mínima se quiseres impacto rápido

Se quiseres ir só pelo que muda mais a perceção do produto:

1. PR 1
2. PR 2
3. PR 3
4. PR 4
5. PR 5
6. PR 6

Esse conjunto já muda bastante o `theone` sem depender de tudo o resto.
