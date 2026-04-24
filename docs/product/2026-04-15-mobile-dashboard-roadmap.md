# TheOne — Relatório de Produto, UI/UX e Roadmap de Execução

Data: 2026-04-15

## 1) Resumo executivo

O repositório `theone` já está **bem mais avançado** do que um MVP cru.

Hoje já existem:
- autenticação com `signup`, `login_email` e seleção de workspace;
- dashboard operacional inicial em `/dashboard`;
- agenda/calendário dedicado;
- analytics próprios;
- customers, services e appointments;
- base de mensageria/WhatsApp com inbound webhook, assinatura, roteamento por tenant e páginas/admin de suporte;
- outbound WhatsApp com provider-backed send quando configurado.

Isto muda a natureza do trabalho:

**o teu problema principal já não é “construir um CRM do zero”; é transformar um backend/ops CRM funcional num produto muito mais claro, bonito, mobile-first e orientado a dono de negócio.**

A tua visão para a home mobile faz sentido e é compatível com o estado atual do repo. O que falta não é só “mais features”; falta sobretudo:
- hierarquia de produto;
- definição de métricas;
- onboarding que personalize a experiência;
- um design system consistente;
- reorganização da home para decisões rápidas;
- simplificação da navegação mobile;
- uma camada financeira mais clara (revenue diário/mensal).

---

## 2) O que existe hoje no `theone`

### 2.1 Auth e sessão
- A página de login já suporta login por email e seleção de workspace quando o email pertence a vários tenants: [`frontend/app/login/page.tsx`](../frontend/app/login/page.tsx)
- A página de registo já cria workspace + conta inicial: [`frontend/app/register/page.tsx`](../frontend/app/register/page.tsx)
- O catálogo funcional do projeto confirma `signup`, `register/login`, `login_email` e `select_workspace`: [`docs/audit/2026-04-09-functional-catalog.md`](../audit/2026-04-09-functional-catalog.md)

### 2.2 Dashboard/home
- A home atual já é um “operational overview” com cards, quick actions e listas curtas: [`frontend/app/dashboard/page.tsx`](../frontend/app/dashboard/page.tsx)
- O documento do próprio repo define que este dashboard atual é operacional, não BI/analytics: [`docs/features/operational-dashboard-mvp.md`](../features/operational-dashboard-mvp.md)
- O contrato atual do dashboard não inclui revenue; inclui contagens operacionais: [`frontend/lib/contracts/dashboard.ts`](../frontend/lib/contracts/dashboard.ts)

### 2.3 Calendar e analytics
- Já existe uma página de calendário bastante rica, com week/day, drag/drop e resize: [`frontend/app/dashboard/calendar/page.tsx`](../frontend/app/dashboard/calendar/page.tsx)
- Já existe página de analytics com overview, services breakdown, heatmap, bookings over time e at-risk customers: [`frontend/app/dashboard/analytics/page.tsx`](../frontend/app/dashboard/analytics/page.tsx)

### 2.4 WhatsApp/messaging
- O repositório já tem rota de webhook Meta com verificação e parsing de eventos: [`app/http/routes/messaging.py`](../../app/http/routes/messaging.py)
- Já existe verificação HMAC para assinatura do webhook: [`modules/messaging/providers/meta_cloud.py`](../../modules/messaging/providers/meta_cloud.py)
- Já existe provider outbound para WhatsApp Cloud API: [`modules/messaging/providers/meta_whatsapp_cloud.py`](../../modules/messaging/providers/meta_whatsapp_cloud.py)
- Já existe fluxo outbound com templates, histórico, deeplink fallback e envio provider-backed: [`app/http/routes/outbound.py`](../../app/http/routes/outbound.py)
- Já existe documentação interna desse outbound MVP: [`docs/features/outbound-basic-mvp.md`](../features/outbound-basic-mvp.md)
- Já existe página admin para mapear `phone_number_id` por tenant: [`frontend/app/dashboard/admin/whatsapp-accounts/page.tsx`](../frontend/app/dashboard/admin/whatsapp-accounts/page.tsx)
- As variáveis de ambiente para webhook + outbound provider já estão previstas no `.env.example`: [`../.env.example`](../../.env.example)

### 2.5 Riscos técnicos já identificados no próprio repo
A auditoria técnica do projeto já aponta blockers importantes antes de escala forte:
- segredos versionados;
- billing in-memory;
- conflito entre RLS e resolução de tenant para inbound WhatsApp;
- ausência de RBAC;
- ausência de observabilidade.

Ver: [`docs/audit/2026-04-09-technical-audit.md`](../audit/2026-04-09-technical-audit.md)

---

## 3) O que tu queres construir de facto

A partir do teu texto, a versão certa do produto parece ser:

### 3.1 Posição do produto
Um **operating system mobile-first para pequenos negócios de serviços**, onde a home responde instantaneamente a estas perguntas:
- quanto faturei hoje?
- quanto faturei este mês?
- quantos bookings tenho hoje?
- o que precisa de ação agora?
- que clientes, mensagens ou confirmações estão pendentes?

### 3.2 Resultado esperado da home
A primeira página não deve ser “uma coleção de widgets”.
Deve ser **uma página de decisão**.

A regra deveria ser:
- primeira linha = estado do negócio;
- segunda linha = agenda do dia;
- terceira linha = ações rápidas;
- quarta linha = follow-ups e sinais de atenção.

---

## 4) Gap analysis: o que falta entre o estado atual e a visão desejada

## 4.1 O que já encaixa na tua visão
- Home operacional já existe.
- Quick actions já existem, mas ainda não estão bem priorizadas.
- Calendar já existe e pode virar a peça principal em tablet/desktop.
- Analytics já existem e permitem puxar parte dos dados necessários.
- WhatsApp já tem base sólida no `theone`.

## 4.2 O que ainda falta

### A) Camada financeira simples e clara
Hoje a home não mostra:
- faturação diária;
- faturação mensal;
- tendência comparativa;
- opção de esconder valores.

### B) Definições de negócio
Ainda não está definido com precisão:
- o que conta como revenue;
- o que conta como booking diário;
- o que conta como “mensagem por responder”;
- o que conta como “trend”.

Sem isto, o dashboard fica bonito mas inconsistente.

### C) Onboarding real
O registo atual cria conta/workspace, mas ainda não existe onboarding de personalização do produto.

### D) UI/UX mais premium e coerente
Login/register funcionam, mas ainda não entregam o “aesthetic” que tu queres.

### E) Home explicitamente mobile-first
Apesar de o projeto ter elementos responsivos, a home ainda está muito baseada em blocos de dashboard genéricos, não num fluxo “thumb-first” de telemóvel.

### F) Priorização de mensagens pendentes
Tu mencionaste “mensagens por responder”. Isso pede:
- inbox/resumo de conversas;
- unread count;
- ação rápida “reply / open conversation”.

Isto não está definido como peça central da home atual.

---

## 5) Definições que precisam existir antes do redesign

Esta parte é crítica. O produto precisa de um glossário real.

## 5.1 Revenue diário
**Definição recomendada (v1):** soma do valor de appointments com status `completed` cuja data de conclusão cai no dia local do tenant.

Motivo:
- é simples;
- é auditável;
- evita contar no-shows/cancelamentos;
- alinha revenue com serviço efetivamente prestado.

## 5.2 Revenue mensal
**Definição recomendada (v1):** soma do valor de appointments `completed` no mês atual do tenant.

## 5.3 Booking diário
**Definição recomendada (v1):** contagem de appointments com `starts_at` dentro do dia atual do tenant, excluindo `cancelled` e opcionalmente mostrando `no_show` à parte.

## 5.4 Mensagens por responder
**Definição recomendada (v1):** conversas em que a última mensagem veio do cliente e ainda não houve resposta da equipa após essa mensagem.

## 5.5 Trends
“Trends” não deve ser um nome vago.

**Definição recomendada (v1):** comparação curta entre o período atual e o período equivalente anterior.
Exemplos:
- bookings hoje vs ontem;
- revenue hoje vs média dos últimos 7 dias;
- revenue mês atual vs mesmo ponto do mês anterior.

## 5.6 Hide revenue
**Definição recomendada (v1):** toggle local do utilizador para mascarar monetários (`€ ••••`).
Não precisa alterar o backend.

---

## 6) O onboarding que tu precisas

O onboarding não deve perguntar “tudo”. Deve perguntar só o que altera a experiência do produto.

## 6.1 Perguntas realmente importantes

### Identidade do negócio
- nome do negócio
- categoria do negócio
- idioma principal
- moeda
- timezone

### Operação
- quantas localizações tens?
- trabalhas sozinho ou em equipa?
- o teu foco principal é bookings, clientes, mensagens ou faturação?

### Agenda
- duração média dos serviços
- horário de funcionamento
- precisas de vista semana, dia ou ambas?

### Comunicação
- queres usar WhatsApp?
- queres lembretes automáticos?
- queres centralizar mensagens na home?

### Home personalization
- o que queres ver primeiro na home?
  - revenue
  - bookings
  - calendar
  - pending messages
  - reactivation / inactive customers

## 6.2 O que NÃO vale a pena perguntar no onboarding inicial
- detalhes avançados de branding;
- automações complexas;
- segmentação profunda;
- preferências raras que podem ficar em settings.

## 6.3 Estrutura do onboarding recomendada
1. **Welcome / promise**
2. **Business profile**
3. **How you work**
4. **Home priorities**
5. **Channels (WhatsApp / email)**
6. **Finish + generate workspace defaults**

---

## 7) Proposta de UX para login/register aesthetic

## 7.1 Objetivo
As telas de entrada devem dizer “produto premium, simples, calmo e confiável”.

## 7.2 Direção visual
- fundo limpo com profundidade suave;
- card central forte;
- tipografia grande e calma;
- poucos campos por vez;
- estados de erro elegantes;
- CTA único e dominante;
- benefícios curtos ao lado em desktop;
- em mobile: foco total no formulário.

## 7.3 Mudanças concretas
### Login
- trocar “Welcome back” por headline com mais identidade;
- mostrar subtítulo contextual (“Run your day from one place” ou equivalente);
- melhorar espaçamento, estados de foco e loading;
- manter seleção de workspace como step 2, mas com mais clareza visual.

### Register
- deixar de ser apenas “cria workspace + conta”;
- tratar como entrada para onboarding;
- separar criação de conta de configuração do negócio.

---

## 8) Home mobile proposta

## 8.1 Princípio
A home mobile deve caber no polegar e priorizar **scan de 5 segundos**.

## 8.2 Ordem recomendada

### Bloco 1 — Header
- saudação curta
- data presente sempre
- seletor de período/local se necessário
- toggle de ocultar revenue

### Bloco 2 — Business snapshot
Dois cards principais:
- **Revenue today**
- **Revenue this month**

Abaixo, uma micro-linha de tendência:
- `+12% vs yesterday`
- `+8% vs same point last month`

### Bloco 3 — Booking snapshot
- bookings today
- pending confirmations
- no-shows / cancellations do dia

### Bloco 4 — Quick actions
Máximo 4 principais:
- Add client
- Add booking
- Open calendar
- Send message / open inbox

Os restantes podem ficar em “More”.

### Bloco 5 — Today timeline
Lista curta dos próximos appointments.
Aqui já tens base reutilizável da home atual e do calendar.

### Bloco 6 — Pending communication
- mensagens por responder
- confirmações pendentes
- follow-ups críticos

### Bloco 7 — Trends / opportunities
- inactive customers
- top service today/week
- online bookings trend

---

## 9) Tablet / grande ecrã

A tua ideia está certa: quando houver espaço, a app deve mudar de “stack de cards” para “workspace”.

## 9.1 Layout recomendado
### Coluna esquerda
- KPIs principais
- quick actions
- pending messages / confirmations

### Coluna central
- calendário (peça principal)

### Coluna direita
- inbox curta / activity / inactive customers / reminders

## 9.2 Regra de responsive
- **mobile**: cards empilhados
- **tablet**: cards + mini calendar
- **desktop**: calendar-first layout

O `theone` já tem um calendário forte o suficiente para isso. O trabalho é colocá-lo na arquitetura certa do produto, não recriá-lo do zero.

---

## 10) Mapa funcional recomendado

## 10.1 Home
- revenue today
- revenue month
- bookings today
- pending confirmations
- quick actions
- upcoming appointments
- pending messages
- inactive customers / trends

## 10.2 Customers
- perfil
- histórico
- outbound history
- tags/stage

## 10.3 Calendar
- day/week
- quick create
- drag/drop
- conflict handling

## 10.4 Messages
- inbox
- unread
- reply
- templates
- delivery state

## 10.5 Analytics
- bookings over time
- service performance
- repeat rate
- at-risk customers
- revenue trends

## 10.6 Settings
- business profile
- team
- calendar preferences
- channels
- billing
- home preferences

---

## 11) O que precisa ser adicionado no backend

## 11.1 Dashboard metrics novas
Criar ou expandir endpoint(s) para devolver:
- `revenue_today`
- `revenue_month`
- `revenue_today_delta_pct`
- `revenue_month_delta_pct`
- `bookings_today`
- `pending_messages_count`
- `pending_confirmations_count`
- `next_appointments[]`

## 11.2 Preferences do utilizador
Guardar preferências como:
- hide_revenue
- home_primary_focus
- preferred_dashboard_layout

## 11.3 Inbox state
Definir modelo/consulta que permita computar:
- unread conversations
- conversations awaiting reply
- last inbound message per conversation

## 11.4 Revenue source of truth
Escolher uma destas estratégias:
1. **derived from completed appointments** (mais rápido para v1)
2. invoices/payments reais (mais enterprise, mais pesado)

Para a tua fase atual, a melhor decisão é **derived from completed appointments**.

---

## 12) O que precisa ser adicionado no frontend

## 12.1 Nova home modelada por blocos
Refatorar a home atual para blocos reutilizáveis:
- `KpiCard`
- `MoneyCard`
- `QuickActionsGrid`
- `TodayAppointmentsList`
- `PendingInboxCard`
- `TrendMiniCard`

## 12.2 Responsive por intenção
Não basta “encolher”.
Cada breakpoint precisa de propósito:
- mobile = action-first
- tablet = plan-the-day
- desktop = operate-the-business

## 12.3 Hide revenue toggle
Estado local persistido por user preference.

## 12.4 Date prominence
A data deve estar visível no topo da home e do calendário.
Hoje o `TopBar` mostra título e user, mas não destaca a data como elemento de orientação diária.

---

## 13) O que precisas de aprender de UI/UX, de forma prática

Tu não precisas virar “designer de Dribbble”.
Precisas dominar 6 fundamentos:

## 13.1 Hierarquia
O utilizador deve perceber em 2 segundos:
- o que é principal;
- o que é secundário;
- o que é clicável.

## 13.2 Spacing
Usa sistema consistente (ex.: 4 / 8 / 12 / 16 / 24 / 32).

## 13.3 Information architecture
Agrupar por tarefa, não por entidade técnica.

## 13.4 States
Todo componente precisa de:
- default
- hover
- focus
- loading
- empty
- error
- success

## 13.5 Responsive thinking
Desenhar mobile primeiro e só depois expandir.

## 13.6 Copy UX
Textos pequenos importam:
- CTA claro
- labels concretas
- empty states honestos
- sem nomes vagos como “Trends” sem contexto.

### Sequência prática de aprendizagem
1. layout and spacing
2. hierarchy and typography
3. cards and lists
4. mobile navigation
5. dashboard patterns
6. onboarding flows

---

## 14) Roadmap de execução recomendado

## Fase 0 — Segurança e base operacional
Antes de embelezar o produto, resolver blockers já identificados:
- remover segredos do repo;
- corrigir billing in-memory;
- corrigir desenho RLS + inbound account lookup;
- mínimo RBAC para ações admin;
- logging/observability básica.

Sem isto, qualquer crescimento de WhatsApp ou produto vai apoiar-se numa base frágil.

## Fase 1 — Definição de produto
Entregáveis:
- glossário de métricas
- definição de revenue
- definição de pending messages
- definição de quick actions oficiais
- definição do onboarding v1

## Fase 2 — Design system mínimo
Entregáveis:
- tokens de spacing
- tipografia
- card patterns
- top bar
- mobile nav
- CTA styles
- form patterns

## Fase 3 — Auth + onboarding redesign
Entregáveis:
- login aesthetic
- register refeito
- onboarding multi-step
- gravação de preferências iniciais do workspace/user

## Fase 4 — Nova home mobile-first
Entregáveis:
- revenue cards
- booking analytics do dia
- quick actions certas
- data sempre visível
- pending messages card
- hidden revenue toggle

## Fase 5 — Tablet/desktop layout
Entregáveis:
- home com calendar-first layout em larguras maiores
- coluna lateral com mensagens por responder
- melhor integração entre overview e calendar

## Fase 6 — Finance / messaging polish
Entregáveis:
- trends comparativas reais
- status de entrega WhatsApp visíveis na UI
- revenue insights
- reminders / automations reais

---

## 15) Prioridade real para os próximos passos

Se eu tivesse de escolher a ordem certa para ti agora, seria:

1. **Definir métricas e onboarding**
2. **Redesenhar login/register**
3. **Refazer a home mobile**
4. **Trazer o calendar para layouts largos**
5. **Subir mensagens pendentes para a home**
6. **Refinar revenue/trends**

---

## 16) Conclusão objetiva

O `theone` já tem backend e produto suficiente para suportar a visão que descreveste.

O que falta agora é menos “inventar mais backend” e mais:
- clareza de produto;
- melhor definição de métricas;
- UX mobile-first;
- design system;
- priorização da home;
- integração mais visível entre dashboard, calendar e messages.

Em resumo:

- **o core existe**;
- **a experiência ainda não está ao nível da ambição**;
- **a home precisa deixar de ser um dashboard genérico e virar um cockpit diário de negócio**.

Esse é o próximo salto do produto.
