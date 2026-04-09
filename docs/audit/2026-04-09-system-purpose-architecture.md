# Visão do Sistema — Propósito, Arquitetura e Lacunas (Beauty CRM)

Data: **2026-04-09**  
Autor: Staff Engineer (levantamento técnico)

## 1) Propósito do sistema

### Evidência explícita
- O repositório se descreve como **“Beauty & Lifestyle SaaS CRM”** e adota um **monólito modular por domínio**. (`docs/architecture/repo-map.md`)
- Há um frontend Next.js identificado como “Beauty CRM Frontend”. (`frontend/README.md`)

### Inferência provável (com base nos módulos/rotas)
- CRM multi-tenant para negócios de beleza (salões/estúdios), com:
  - clientes, histórico de interações e pipeline
  - agenda (appointments) e catálogo de serviços
  - multi-unidades (locations) e configuração por tenant
  - inbound WhatsApp (webhook) com persistência de mensagens/conversas
  - métricas/analytics operacionais

### Hipóteses que precisam confirmação
- “Automações” como feature de produto (há gate/limites, mas não foi observado módulo/rotas completas).
- Requisitos enterprise (SLO/SLA, compliance, RBAC) — há indícios em docs, mas partes estão incompletas.

## 2) Mapa da arquitetura (alto nível)

### 2.1 Camada HTTP (API)
- Framework: **FastAPI**
- Entry point ASGI: `main.py` (compatibilidade) e factory em `app/http/main.py`
- Middlewares e handlers:
  - CORS
  - normalização de erros (domínio/HTTP/pydantic)
  - middleware de tenancy por header (com bypass para rotas públicas e webhook inbound)
- Routers por domínio (prefixos):
  - `/auth`, `/crm`, `/analytics`, `/billing`, `/messaging`, `/tenants`

### 2.2 Container (injeção de dependências simplificada)
- O container monta repos e services e expõe via `app.state.container`.
- Wiring atual (alto nível):
  - Tenants: `SqlTenantRepo` + `TenantService`
  - IAM: `SqlUserRepo` + `AuthService`
  - CRM: `SqlCrmRepo` + `CrmService`
  - Analytics: `SqlAnalyticsRepo` + `AnalyticsService`
  - Messaging: `SqlMessagingRepo` + `InboundWebhookService` (+ `InboundMessagingService` legado)
  - Billing: `InMemoryBillingRepo` + `BillingService`

### 2.3 Core (cross-cutting)
- Config: `core/config/*` (`AppConfig`)
- Tenancy context: `core/tenancy/*` (ContextVar `tenant_id`)
- Auth context: `core/auth/*` (ContextVar `user_id`)
- Errors: `core/errors/*` (erros tipados + mapeamento HTTP)
- DB session: `core/db/session.py` (SQLAlchemy session com `set_config('app.current_tenant_id', ...)` no Postgres)
- Observabilidade: `core/observability/*` (**stubs vazios no estado atual**)

### 2.4 Domínios (modules/*)
- `modules/tenants`: tenants + settings
- `modules/iam`: users e autenticação por tenant (persistência via repo SQL)
- `modules/crm`: customers, interactions, pipeline, locations, services, appointments, calendar
- `modules/messaging`: inbound webhook, WhatsApp accounts, webhook_events, conversations, messages
- `modules/billing`: planos/limites/feature gates (persistência **in-memory**)
- `modules/analytics`: métricas (parte via service, parte via queries no router)
- `modules/audit`: `audit_log` + snapshot de mudanças

### 2.5 Persistência e migrations
- ORM: SQLAlchemy
- Migrations: Alembic em `alembic/versions/*`
- Multi-tenancy:
  - Contexto via header (API) + ContextVar
  - No Postgres, RLS/policies são usadas em várias tabelas (incl. customers/interactions/messaging/etc.)
  - Em `DATABASE_URL=dev`, é usado SQLite in-memory (sem RLS), com `create_all()` automático

### 2.6 Assíncrono / background
- Queue: Celery + Redis
- Uso atual: inbound webhook enfileira task; worker processa com retry/backoff e marca DLQ (“dead_letter”) em falhas persistentes.

### 2.7 Frontend
- Next.js + Axios
- Sessão em `localStorage` + cookies (`token`, `tenant_id`)
- Middleware do Next protege rotas `/dashboard/*`

## 3) Fluxos end-to-end principais (observados)

### 3.1 Request autenticado “normal” (dashboard)
1) Cliente envia `X-Tenant-ID` + `Authorization: Bearer <token>`.
2) Middleware de tenancy seta `tenant_id` no ContextVar.
3) `require_user` valida token HMAC e verifica `tenant_id` do token vs header.
4) `db_session()` abre sessão e (em Postgres) seta `app.current_tenant_id`.
5) Repos/queries aplicam filtros e/ou RLS, retornando dados do tenant.

### 3.2 Signup + primeiro acesso
1) `POST /auth/signup` cria tenant + user.
2) Retorna token e tenant_id.
3) Frontend salva token/tenant e redireciona para dashboard.

### 3.3 Inbound webhook (WhatsApp)
1) `POST /messaging/inbound` recebe payload, valida assinatura (Meta Cloud API).
2) Resolve o tenant via mapeamento `whatsapp_accounts`.
3) Enfileira Celery task.
4) Worker grava evento, deduplica, cria conversa/mensagem e adiciona interação no CRM.

## 4) Lacunas e dúvidas relevantes (para governança e evolução)

- **Documentação essencial vazia:** `README.md`, `DECISIONS.md`, `PROJECT_RULES.md`, `docs/runbooks/*` (impacta onboarding e operação).
- **Observabilidade ausente:** stubs vazios em `core/observability/*`.
- **RBAC/permissões ausentes:** não há autorização granular para ações sensíveis (ex.: mudança de plano).
- **Billing in-memory:** risco elevado em ambientes com múltiplos processos/réplicas e worker separado.
- **RLS vs resolução de tenant em webhook:** requer validação cuidadosa (lookup antes de existir tenant context).
- **Infra local incompleta:** `docker-compose.yml` só tem Postgres; Redis/worker não estão definidos.

## 4.1 Contradições arquiteturais (as-is) que afetam produção

### (C3) RLS vs roteamento de inbound webhook (Confirmado)
- O inbound webhook precisa resolver tenant via `whatsapp_accounts` antes de ter tenant context.
- Se `whatsapp_accounts` estiver sob RLS com policy baseada em `current_setting('app.current_tenant_id')`, o lookup pode falhar.
- Isto é uma contradição entre “hard isolation por RLS” e “roteamento por lookup global”.
- Ver detalhes e opções de correção: `docs/audit/2026-04-09-technical-audit.md` (C3).

### (C2) Billing in-memory vs arquitetura multi-process (Confirmado)
- A API expõe endpoint para alterar plano, mas o estado é in-memory.
- Workers e API (processos separados) não compartilham estado, tornando gates de feature não determinísticos.
- Ver detalhes: `docs/audit/2026-04-09-technical-audit.md` (C2).


## 5) Referências rápidas (arquivos-chave)

- API factory e middleware: `app/http/main.py`
- Rotas:
  - Auth: `app/http/routes/auth.py`
  - CRM: `app/http/routes/crm.py`
  - Analytics: `app/http/routes/analytics.py`
  - Billing: `app/http/routes/billing.py`
  - Messaging: `app/http/routes/messaging.py`
  - Tenants: `app/http/routes/tenants.py`
- Queue/worker: `tasks/queue.py`, `tasks/workers/messaging/inbound_worker.py`
- DB session / tenant context: `core/db/session.py`, `core/tenancy/*`
- Migrations: `alembic/versions/*`
- Frontend client/auth: `frontend/lib/api.ts`, `frontend/lib/auth.ts`, `frontend/middleware.ts`
