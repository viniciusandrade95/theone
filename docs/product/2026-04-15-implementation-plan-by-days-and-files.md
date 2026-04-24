# TheOne — Plano de Implementação por Dias e por Ficheiros

Data: 2026-04-15

## 1) Como usar este documento

Este plano pega no roadmap de produto e transforma-o em execução concreta.

Tens duas formas de usar:
- **por dias**: se quiseres trabalhar em sprint sequencial;
- **por ficheiros**: se quiseres abrir o repo e avançar ficheiro a ficheiro.

Este plano assume o seguinte:
- estás a trabalhar **dentro do repo `viniciusandrade95/theone`**;
- queres primeiro fazer a base certa e só depois polir;
- queres uma home mobile-first, onboarding real, auth mais aesthetic e melhor surface para revenue, bookings e mensagens pendentes.

---

## 2) Ordem certa de execução

### Ordem recomendada
1. definir métricas e contrato da home
2. preparar estrutura UI/shared components
3. refazer login/register
4. criar onboarding
5. refazer home mobile
6. subir mensagens pendentes
7. melhorar tablet/desktop com calendário
8. polir revenue/trends e delivery states

### Regra importante
Não comeces por mexer no visual da home sem antes fechar:
- definição de `revenue_today`
- definição de `revenue_month`
- definição de `pending_messages_count`
- definição de quick actions oficiais

Se não fizeres isso primeiro, vais redesenhar duas vezes.

---

# PARTE A — PLANO POR DIAS

## Dia 1 — Fechar definições de produto e contratos

## Objetivo
Congelar o significado das métricas e o shape da nova home.

## Tarefas
- definir oficialmente:
  - `revenue_today`
  - `revenue_month`
  - `bookings_today`
  - `pending_confirmations_count`
  - `pending_messages_count`
  - `trend` e `delta_pct`
- decidir a source of truth de revenue v1:
  - **appointments completed**
- decidir quick actions oficiais da home:
  - add client
  - add booking
  - open calendar
  - open inbox / send message
- decidir quais blocos ficam na home mobile v1

## Ficheiros a tocar
### Atualizar
- `docs/product/2026-04-15-mobile-dashboard-roadmap.md`
- `docs/features/operational-dashboard-mvp.md`
- `frontend/lib/contracts/dashboard.ts`
- `app/http/routes/dashboard.py`

### Criar
- `docs/product/dashboard-metrics-glossary.md`
- `docs/product/home-v1-information-architecture.md`

## Resultado esperado no fim do dia
- existe um glossário claro de métricas
- o contrato TS e o endpoint já sabem que a home nova vai precisar de revenue e pending messages

---

## Dia 2 — Preparar o backend da nova home

## Objetivo
Expandir o endpoint `/dashboard/overview` para suportar a home que queres.

## Tarefas
- adicionar ao response model:
  - `revenue_today`
  - `revenue_month`
  - `revenue_today_delta_pct`
  - `revenue_month_delta_pct`
  - `pending_messages_count`
  - `next_appointments`
- implementar cálculo de revenue v1 a partir de appointments concluídos
- deixar comentários/documentação claros no código para explicar limitações
- manter compatibilidade com a home atual enquanto refatoras o frontend

## Ficheiros a tocar
### Atualizar
- `app/http/routes/dashboard.py`
- `frontend/lib/contracts/dashboard.ts`
- `tests/api/test_dashboard_overview_api.py`

### Possivelmente criar
- `modules/analytics/service/dashboard_metrics_service.py`

> Se quiseres manter o router mais limpo, move parte da lógica para service. Se não, mantém no router nesta fase e refatora depois.

## Resultado esperado no fim do dia
- backend já responde com as métricas novas
- tens testes mínimos para não partir o overview

---

## Dia 3 — Criar a base visual compartilhada

## Objetivo
Montar os componentes reutilizáveis antes de refazer páginas grandes.

## Tarefas
- criar componentes base para cards da home
- criar variante de money card com hidden state
- criar grid de quick actions
- criar bloco de section header
- padronizar spacing e headings

## Ficheiros a tocar
### Criar
- `frontend/components/dashboard/KpiCard.tsx`
- `frontend/components/dashboard/MoneyCard.tsx`
- `frontend/components/dashboard/QuickActionsGrid.tsx`
- `frontend/components/dashboard/SectionHeader.tsx`
- `frontend/components/dashboard/TodayAppointmentsList.tsx`
- `frontend/components/dashboard/PendingInboxCard.tsx`
- `frontend/components/dashboard/TrendMiniCard.tsx`

### Atualizar
- `frontend/components/dashboard/DashboardLayout.tsx`
- `frontend/components/dashboard/TopBar.tsx`

## Resultado esperado no fim do dia
- tens uma mini-library da home
- para de duplicar card UI diretamente em `page.tsx`

---

## Dia 4 — Melhorar navegação mobile e top bar

## Objetivo
Fazer a shell parecer produto mobile-first, não dashboard genérico.

## Tarefas
- tornar a data visível no topo
- mostrar contexto do dia e, se necessário, location atual
- rever a prioridade do menu mobile
- reduzir ruído no top bar
- preparar espaço para toggle de hide revenue

## Ficheiros a tocar
### Atualizar
- `frontend/components/dashboard/TopBar.tsx`
- `frontend/components/dashboard/MobileNav.tsx`
- `frontend/components/dashboard/SidebarNav.tsx`
- `frontend/components/dashboard/DashboardLayout.tsx`
- `frontend/app/dashboard/layout.tsx`
- `frontend/lib/default-location.tsx`

## Resultado esperado no fim do dia
- top bar comunica “hoje / operação / contexto”
- mobile nav passa a refletir as prioridades do produto

---

## Dia 5 — Refazer a home mobile

## Objetivo
Transformar `/dashboard` numa home orientada a decisão rápida.

## Tarefas
- reorganizar a home em blocos:
  - header contextual
  - revenue today / month
  - booking snapshot
  - quick actions
  - next appointments
  - pending messages
  - opportunities / inactive customers
- substituir cards antigos por componentes novos
- manter estados de loading, error e empty state elegantes

## Ficheiros a tocar
### Atualizar
- `frontend/app/dashboard/page.tsx`
- `frontend/lib/contracts/dashboard.ts`

### Usar os componentes novos
- `frontend/components/dashboard/KpiCard.tsx`
- `frontend/components/dashboard/MoneyCard.tsx`
- `frontend/components/dashboard/QuickActionsGrid.tsx`
- `frontend/components/dashboard/TodayAppointmentsList.tsx`
- `frontend/components/dashboard/PendingInboxCard.tsx`
- `frontend/components/dashboard/TrendMiniCard.tsx`

## Resultado esperado no fim do dia
- home mobile nova já existe
- revenue e bookings aparecem logo acima
- quick actions ficam claramente visíveis

---

## Dia 6 — Login aesthetic

## Objetivo
Levar a página de login para um nível visual mais premium.

## Tarefas
- melhorar hierarchy visual
- melhorar headline/subheadline
- melhorar campos e estados de erro/loading
- melhorar step de seleção de workspace
- garantir consistência com o resto da app

## Ficheiros a tocar
### Atualizar
- `frontend/app/login/page.tsx`
- `frontend/components/ui/card.tsx` (se precisares de pequenas melhorias globais)
- `frontend/components/ui/input.tsx` (se precisares de consistência visual)
- `frontend/lib/auth.ts` (apenas se mexeres na persistência/UX de sessão)

## Resultado esperado no fim do dia
- login deixa de parecer só funcional
- seleção de workspace continua clara e mais bonita

---

## Dia 7 — Register + base do onboarding

## Objetivo
Parar de tratar o register como fim do fluxo. Ele deve ser só a entrada.

## Tarefas
- refazer register visualmente
- decidir se onboarding começa logo após signup ou se ocupa parte do register
- criar estrutura mínima do onboarding v1

## Ficheiros a tocar
### Atualizar
- `frontend/app/register/page.tsx`

### Criar
- `frontend/app/onboarding/page.tsx`
- `frontend/components/onboarding/OnboardingStepper.tsx`
- `frontend/components/onboarding/BusinessProfileStep.tsx`
- `frontend/components/onboarding/HowYouWorkStep.tsx`
- `frontend/components/onboarding/HomePrioritiesStep.tsx`
- `frontend/components/onboarding/ChannelsStep.tsx`
- `frontend/components/onboarding/FinishStep.tsx`

## Resultado esperado no fim do dia
- onboarding já existe visualmente, mesmo que ainda não persista tudo

---

## Dia 8 — Persistir onboarding e preferências

## Objetivo
Guardar as escolhas do onboarding para personalizar a home.

## Tarefas
- definir onde guardar preferências:
  - tenant settings
  - ou user preferences separadas
- persistir:
  - hide_revenue
  - home_primary_focus
  - preferred_dashboard_layout
  - wants_whatsapp
  - wants_reminders
- gerar defaults no final do onboarding

## Ficheiros a tocar
### Atualizar
- `app/http/routes/auth.py`
- `app/http/routes/crm.py` ou settings routes existentes
- `modules/tenants/repo/settings_sql.py`
- `modules/tenants/models/tenant_settings_orm.py`
- `frontend/app/onboarding/page.tsx`
- `frontend/lib/contracts/settings.ts`

### Criar se faltar estrutura própria de preferências do user
- `app/http/routes/preferences.py`
- `modules/iam/models/user_preferences_orm.py`
- `modules/iam/repo/user_preferences_sql.py`
- migration Alembic correspondente

## Resultado esperado no fim do dia
- onboarding grava dados reais
- home pode ler preferências e adaptar-se

---

## Dia 9 — Mensagens pendentes na home

## Objetivo
Trazer “mensagens por responder” para a superfície principal do produto.

## Tarefas
- definir consulta/backend para:
  - unread conversations
  - awaiting reply
  - última mensagem inbound por conversa
- criar bloco visual resumido na home
- ligar com navegação para inbox / outbound / customer

## Ficheiros a tocar
### Atualizar
- `app/http/routes/dashboard.py`
- `app/http/routes/messaging.py`
- `app/http/routes/outbound.py`
- `frontend/app/dashboard/page.tsx`
- `frontend/components/dashboard/PendingInboxCard.tsx`

### Criar se ainda não existir endpoint próprio
- `app/http/routes/inbox.py`
- `frontend/app/dashboard/inbox/page.tsx`
- `frontend/lib/contracts/inbox.ts`

## Resultado esperado no fim do dia
- a home já mostra trabalho pendente real, não só números

---

## Dia 10 — Tablet e desktop com calendário

## Objetivo
Fazer a home escalar bem em ecrãs maiores.

## Tarefas
- criar layout diferente para `lg/xl`
- trazer mini calendar ou calendar block para a home em larguras grandes
- mover pending messages para coluna lateral
- manter mobile simples e empilhado

## Ficheiros a tocar
### Atualizar
- `frontend/app/dashboard/page.tsx`
- `frontend/app/dashboard/calendar/page.tsx`
- `frontend/components/dashboard/DashboardLayout.tsx`
- `frontend/components/dashboard/TopBar.tsx`

### Criar se precisares de composição separada
- `frontend/components/dashboard/DesktopHomeLayout.tsx`
- `frontend/components/dashboard/HomeCalendarPreview.tsx`
- `frontend/components/dashboard/HomeRightRail.tsx`

## Resultado esperado no fim do dia
- mobile continua limpo
- tablet/desktop ganha aspecto de workspace

---

## Dia 11 — Trends, revenue polish e estados de entrega

## Objetivo
Polir os sinais de negócio e comunicação.

## Tarefas
- mostrar delta percentuais de revenue e bookings
- mostrar top trend útil, não vago
- mostrar estados de delivery WhatsApp mais visíveis
- ligar essas infos a customer/outbound history

## Ficheiros a tocar
### Atualizar
- `frontend/app/dashboard/page.tsx`
- `frontend/app/dashboard/analytics/page.tsx`
- `frontend/components/dashboard/TrendMiniCard.tsx`
- `frontend/app/dashboard/customers/[id]/page.tsx` se existir
- `app/http/routes/outbound.py`

## Resultado esperado no fim do dia
- a home já transmite inteligência, não só estado operacional

---

## Dia 12 — QA, limpeza e documentação final

## Objetivo
Fechar a sprint sem deixar dívida invisível.

## Tarefas
- rever loading/empty/error states
- rever textos UX
- rever responsive
- rever nomes de quick actions
- atualizar docs
- correr e atualizar testes mais afetados

## Ficheiros a tocar
### Atualizar
- `docs/features/operational-dashboard-mvp.md`
- `docs/product/home-v1-information-architecture.md`
- `tests/api/test_dashboard_overview_api.py`
- `tests/api/test_inbound_webhook.py` se houver impactos indiretos
- `tests/api/test_outbound_provider_lifecycle_api.py` se mexeres em messaging surface

## Resultado esperado no fim do dia
- tens uma v1 apresentável, consistente e documentada

---

# PARTE B — PLANO POR FICHEIROS

## 1) Backend — dashboard e métricas

## `app/http/routes/dashboard.py`
### Fazer
- expandir o response model do dashboard
- adicionar revenue diário e mensal
- adicionar deltas percentuais
- adicionar pending messages count
- adicionar `next_appointments` se quiseres separá-los de `appointments_today`
- manter notas honestas sobre limitações

### Ordem interna sugerida
1. criar novos campos no `BaseModel`
2. implementar queries/agregações
3. preencher o response final
4. atualizar testes

---

## `frontend/lib/contracts/dashboard.ts`
### Fazer
- alinhar tipos TS com o novo response
- criar tipos para money metrics
- criar tipos para pending messages summary
- remover ambiguidade de nomes

---

## `tests/api/test_dashboard_overview_api.py`
### Fazer
- adicionar asserts para revenue
- adicionar asserts para pending messages
- adicionar asserts para compatibilidade com timezone

---

## 2) Frontend — home e shell

## `frontend/app/dashboard/page.tsx`
### Fazer
- deixar de ser um ficheiro “gigante com tudo inline”
- passar a orquestrar blocos/componentes
- renderizar a home por secções
- suportar responsive por intenção
- mostrar revenue com hide toggle
- mostrar data/contexto do dia logo acima

### Ordem interna sugerida
1. extrair quick actions
2. extrair cards principais
3. extrair timeline
4. extrair pending messages
5. reorganizar layout por breakpoints

---

## `frontend/components/dashboard/DashboardLayout.tsx`
### Fazer
- ajustar paddings para mobile-first
- garantir que a shell suporta home mais rica sem parecer apertada
- preparar right rail / large screen composition se necessário

---

## `frontend/components/dashboard/TopBar.tsx`
### Fazer
- colocar data em destaque
- mostrar menos ruído técnico
- suportar hide revenue toggle ou deixar espaço para isso
- alinhar títulos com o novo produto

---

## `frontend/components/dashboard/MobileNav.tsx`
### Fazer
- rever ordem dos itens
- garantir que Home/Calendar/Customers/Messages ficam mais centrais
- reduzir labels menos prioritárias no topo do menu

---

## `frontend/app/dashboard/layout.tsx`
### Fazer
- manter `RequireAuth`
- manter `DefaultLocationProvider`
- adicionar providers novos se onboarding/preferences precisarem

---

## `frontend/lib/default-location.tsx`
### Fazer
- garantir que a location default pode ser mostrada na top bar/home
- expor `refresh` quando onboarding/settings alterarem a default location

---

## 3) Novos componentes da home

## `frontend/components/dashboard/KpiCard.tsx`
### Fazer
- card pequeno para contagens
- suportar label, value, hint, trend badge

## `frontend/components/dashboard/MoneyCard.tsx`
### Fazer
- suportar valor monetário
- suportar hidden state
- suportar delta e label secundária

## `frontend/components/dashboard/QuickActionsGrid.tsx`
### Fazer
- 4 ações principais
- opção “More” quando necessário

## `frontend/components/dashboard/TodayAppointmentsList.tsx`
### Fazer
- reutilizar visual de appointments num bloco mais compacto
- focar nos próximos appointments do dia

## `frontend/components/dashboard/PendingInboxCard.tsx`
### Fazer
- unread count
- awaiting reply count
- links rápidos

## `frontend/components/dashboard/TrendMiniCard.tsx`
### Fazer
- trend curta e explicável
- nunca usar nome vago sem contexto

---

## 4) Auth e onboarding

## `frontend/app/login/page.tsx`
### Fazer
- melhorar aesthetic geral
- melhorar microcopy
- tornar o workspace step mais claro
- manter a lógica atual intacta enquanto melhoras a UI

## `frontend/app/register/page.tsx`
### Fazer
- transformar em entrada para onboarding
- melhorar spacing, hierarchy e CTA
- eventualmente redirecionar para `/onboarding`

## `frontend/app/onboarding/page.tsx`
### Fazer
- criar stepper
- pedir apenas dados essenciais
- no fim, persistir preferências/settings

## Componentes onboarding
### Criar
- `frontend/components/onboarding/OnboardingStepper.tsx`
- `frontend/components/onboarding/BusinessProfileStep.tsx`
- `frontend/components/onboarding/HowYouWorkStep.tsx`
- `frontend/components/onboarding/HomePrioritiesStep.tsx`
- `frontend/components/onboarding/ChannelsStep.tsx`
- `frontend/components/onboarding/FinishStep.tsx`

---

## 5) Preferências e settings

## `modules/tenants/models/tenant_settings_orm.py`
### Fazer
- adicionar campos novos se a tabela de settings for o storage escolhido
- exemplos:
  - `home_primary_focus`
  - `preferred_dashboard_layout`
  - `wants_whatsapp`
  - `wants_reminders`

## `modules/tenants/repo/settings_sql.py`
### Fazer
- suportar leitura/escrita dos novos campos
- garantir defaults sensatos

## `frontend/lib/contracts/settings.ts`
### Fazer
- refletir os novos campos no TS

## `frontend/app/dashboard/settings/...`
### Fazer
- dar ao utilizador forma de editar depois o que escolheu no onboarding

---

## 6) Messaging e inbox surface

## `app/http/routes/messaging.py`
### Fazer
- não necessariamente mudar o core do webhook agora
- mas preparar outputs que suportem inbox/resumo se precisares

## `app/http/routes/outbound.py`
### Fazer
- expor de forma mais amigável delivery status para a UI
- garantir filtros e payload suficientes para customer history / inbox summary

## `frontend/app/dashboard/admin/whatsapp-accounts/page.tsx`
### Fazer
- mais tarde, melhorar UX da ligação WhatsApp
- mostrar estado da conexão, não só formulário técnico

---

## 7) Calendar e desktop composition

## `frontend/app/dashboard/calendar/page.tsx`
### Fazer
- reutilizar partes da experiência do calendário na home grande
- criar preview ou bloco resumido para home desktop/tablet

## `frontend/components/dashboard/DesktopHomeLayout.tsx`
### Criar se necessário
- left rail: KPIs + quick actions
- center: calendar preview
- right rail: pending messages + activity

---

# PARTE C — CHECKLIST SUPER PRÁTICA

## Semana 1
- [ ] fechar glossário de métricas
- [ ] expandir backend do dashboard
- [ ] atualizar contrato TS
- [ ] criar componentes base da home
- [ ] melhorar top bar + mobile nav
- [ ] refazer `/dashboard`

## Semana 2
- [ ] refazer login
- [ ] refazer register
- [ ] criar onboarding
- [ ] persistir preferências
- [ ] subir pending messages para home
- [ ] criar layout desktop/tablet
- [ ] polir trends / revenue states / docs

---

# PARTE D — O QUE EU FARIA PRIMEIRO, SEM HESITAR

Se fores abrir o repo hoje e quiseres a ordem mais eficiente, faz assim:

## Bloco 1
- `app/http/routes/dashboard.py`
- `frontend/lib/contracts/dashboard.ts`
- `tests/api/test_dashboard_overview_api.py`

## Bloco 2
- `frontend/components/dashboard/TopBar.tsx`
- `frontend/components/dashboard/MobileNav.tsx`
- `frontend/components/dashboard/DashboardLayout.tsx`

## Bloco 3
- criar componentes novos da home
- refazer `frontend/app/dashboard/page.tsx`

## Bloco 4
- `frontend/app/login/page.tsx`
- `frontend/app/register/page.tsx`
- onboarding

## Bloco 5
- settings/preferences
- pending messages
- desktop calendar composition

---

## 3) Conclusão prática

Sim: a melhor forma de executar isto é **por dias primeiro e por ficheiros depois**.

Porquê:
- por dias, consegues manter foco de produto;
- por ficheiros, consegues executar sem te perder no repo.

Se estiveres com pressa, a sequência mínima para veres impacto rápido é:
1. `dashboard.py`
2. `dashboard.ts`
3. nova home em `frontend/app/dashboard/page.tsx`
4. `TopBar.tsx`
5. `login/page.tsx`
6. `register/page.tsx`

Esse conjunto já muda muito a perceção do produto.
