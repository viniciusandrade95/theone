# Catálogo de Funcionalidades — Backend e Frontend (Beauty CRM)

Data: **2026-04-09**  
Autor: Analista/Staff Engineer (documentação técnica)

> Nota: este catálogo documenta funcionalidades **observadas no código**. Onde houver dúvidas, elas aparecem explicitamente em “Riscos, limitações e dúvidas”.

## Convenções
- “Tenant header”: `X-Tenant-ID` (configurável via `TENANT_HEADER`, mas hardcoded em alguns pontos).
- Autenticação: `Authorization: Bearer <token>` (token HMAC custom).

## Como usar este documento (company-grade)

- Este catálogo descreve **o que existe**. Para “o que mudar e porquê”, ver:
  - `docs/audit/2026-04-09-technical-audit.md`
  - `docs/audit/2026-04-09-project-assessment-executive-summary-risk-register-roadmap.md`
- Para rastreabilidade (feature ↔ rotas ↔ tabelas ↔ testes), ver:
  - `docs/audit/2026-04-09-traceability-matrix.md`

---

## F01 — Inicialização da API (FastAPI) + CORS + Routers

- **Descrição:** Cria instância FastAPI, configura CORS, handlers de exceção e registra routers por domínio.
- **Objetivo:** Disponibilizar API HTTP consistente para o produto.
- **Fluxo principal:**
  1) `load_config()` → carrega envs.
  2) `build_container()` → monta dependências e injeta em `app.state.container`.
  3) Middleware CORS e handlers globais.
  4) Include routers (`/auth`, `/crm`, `/analytics`, `/billing`, `/messaging`, `/tenants`).
- **Entradas:** env vars (app/db/cors/segurança), request HTTP.
- **Saídas:** API servindo endpoints.
- **Regras de negócio:** N/A (infra).
- **Módulos/arquivos envolvidos:** `app/http/main.py`, `main.py`, `core/config/*`, `app/container.py`.
- **Dependências externas:** FastAPI/Starlette/Uvicorn.
- **Riscos, limitações e dúvidas:** runbooks vazios; CORS depende de regex/origins configurados.

---

## F02 — Normalização de erros HTTP (contrato de erro)

- **Descrição:** Normaliza erros de domínio e de validação para payloads previsíveis.
- **Objetivo:** Evitar respostas divergentes e simplificar consumo no frontend.
- **Fluxo principal:**
  1) `AppError`/erros de domínio → `to_http_error()`.
  2) `HTTPException` → `from_http_exception()`.
  3) `RequestValidationError` → resposta 422 com `errors` e `fields` quando possível.
- **Entradas:** exceções levantadas durante requests.
- **Saídas:** JSON `{ error: <CODE>, details?: {...} }`.
- **Regras de negócio:** códigos por status (`401/403/404/409/...`).
- **Módulos/arquivos envolvidos:** `core/errors/http.py`, `core/errors/domain.py`, `app/http/main.py`.
- **Dependências externas:** FastAPI/Pydantic.
- **Riscos, limitações e dúvidas:** múltiplas formas de erro (details/detail/message) exigem tolerância no cliente.

---

## F03 — Tenancy por header + ContextVar (request scope)

- **Descrição:** Extrai tenant do header e mantém em `ContextVar` durante o request.
- **Objetivo:** Isolar dados e regras por tenant.
- **Fluxo principal:**
  1) Middleware ignora `OPTIONS` e endpoints de docs.
  2) Define “rotas públicas” (signup/login_email/select_workspace) e bypass para `/messaging/inbound`.
  3) Exige header `TENANT_HEADER` e chama `set_tenant_id()`.
  4) Limpa tenant/user ao final.
- **Entradas:** headers do request.
- **Saídas:** `tenant_id` disponível via `require_tenant_id()`.
- **Regras de negócio:** rotas públicas e inbound não exigem tenant header.
- **Módulos/arquivos envolvidos:** `app/http/main.py`, `core/tenancy/context.py`, `core/tenancy/enforcement.py`, `core/auth/context.py`.
- **Dependências externas:** N/A.
- **Riscos, limitações e dúvidas:** validação de existência do tenant está comentada; mudança de `TENANT_HEADER` não é propagada a todos os locais.

---

## F04 — DB session (SQLAlchemy) com tenant context (Postgres set_config)

- **Descrição:** Gerencia sessão SQLAlchemy e, em Postgres, configura `app.current_tenant_id` para suportar RLS.
- **Objetivo:** Reforçar isolamento multi-tenant no banco.
- **Fluxo principal:**
  1) `_get_engine()` cria engine conforme `DATABASE_URL` (sqlite in-memory se `dev`).
  2) `db_session()` abre sessão, seta variável de sessão no Postgres se houver tenant no ContextVar.
  3) Commit/rollback/close automático.
- **Entradas:** `DATABASE_URL`, `tenant_id` no ContextVar.
- **Saídas:** sessão pronta para repos/queries.
- **Regras de negócio:** `DATABASE_URL=dev` cria schema automático via `create_all()`.
- **Módulos/arquivos envolvidos:** `core/db/session.py`, `core/config/loader.py`, `alembic/env.py`.
- **Dependências externas:** SQLAlchemy, psycopg, Postgres/SQLite.
- **Riscos, limitações e dúvidas:** comportamento diverge em sqlite (sem RLS); cobertura de RLS depende das migrations.

---

## F05 — Emissão/validação de token (HMAC custom) + PreAuth (seleção de workspace)

- **Descrição:** Token stateless assinado com HMAC; PreAuth token para seleção de workspace.
- **Objetivo:** Autenticar requests e suportar login global com múltiplos tenants.
- **Fluxo principal:**
  - `issue_token()` / `verify_token()`
  - `issue_preauth_token()` / `verify_preauth_token()`
- **Entradas:** `SECRET_KEY`, claims (tenant/user/email/choices), tempo de expiração.
- **Saídas:** strings de token e objetos `AuthToken`/`PreAuthToken`.
- **Regras de negócio:** expiração obrigatória; assinatura obrigatória.
- **Módulos/arquivos envolvidos:** `app/auth_tokens.py`.
- **Dependências externas:** N/A.
- **Riscos, limitações e dúvidas:** sem refresh/revogação/rotação; não é JWT.

---

## F06 — Auth: Signup (novo tenant + primeiro usuário)

- **Descrição:** Cria tenant e usuário inicial, retorna token.
- **Objetivo:** Onboarding self-service.
- **Fluxo principal:**
  1) Gera `tenant_id` UUID.
  2) Seta `tenant_id` no contexto antes do DB session (compatível com RLS).
  3) Cria tenant, registra user, garante default location.
  4) Emite token.
- **Entradas:** `{ tenant_name, email, password }`.
- **Saídas:** `{ tenant_id, user_id, email, token }`.
- **Regras de negócio:** password mínimo; default location garantida.
- **Módulos/arquivos envolvidos:** `app/http/routes/auth.py`, `modules/tenants/service/tenant_service.py`, `modules/iam/service/auth_service.py`, `modules/crm/repo_locations.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** validação de provisionamento/limites não está clara para “primeiro user”; RBAC ausente.

---

## F07 — Auth: Register/Login por tenant + Me

- **Descrição:** Registro e login exigindo tenant header; endpoint `/me`.
- **Objetivo:** Auth “clássico” quando tenant é conhecido.
- **Fluxo principal:**
  - `POST /auth/register` (cria tenant se não existir, registra user, token)
  - `POST /auth/login` (valida credenciais e retorna token)
  - `GET /auth/me` (retorna dados do user)
- **Entradas:** tenant header, bearer token, body (email/password).
- **Saídas:** `AuthOut`/`MeOut`.
- **Regras de negócio:** `require_user` valida `tenant_mismatch` (token vs header).
- **Módulos/arquivos envolvidos:** `app/http/routes/auth.py`, `app/http/deps.py`, `modules/iam/repo/sql.py`.
- **Dependências externas:** DB, hashing PBKDF2.
- **Riscos, limitações e dúvidas:** `register` cria tenant com `name=tenant_id` (pode gerar tenants “lixo”).

---

## F08 — Auth: Login global por e-mail + seleção de workspace

- **Descrição:** Login sem tenant header; se múltiplos tenants, retorna lista de workspaces e exige seleção.
- **Objetivo:** UX para multi-workspace por usuário.
- **Fluxo principal:**
  1) `/auth/login_email` lista users por e-mail e valida senha.
  2) Se único tenant → token direto.
  3) Se múltiplos → `preauth_token` + lista de workspaces.
  4) `/auth/select_workspace` valida `preauth_token` e emite token final.
- **Entradas:** `{email,password}`; depois `{preauth_token, tenant_id}`.
- **Saídas:** `LoginEmailOut` ou `AuthOut`.
- **Regras de negócio:** `preauth_token` expira; workspace deve estar em `choices`.
- **Módulos/arquivos envolvidos:** `app/http/routes/auth.py`, `app/auth_tokens.py`, `modules/iam/repo/sql.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** sem rate limiting; enumeração de workspaces sob credenciais válidas (avaliar requisito).

---

## F09 — Provisionamento de tenant via API (autenticado)

- **Descrição:** Cria tenant informando `id` e `name`.
- **Objetivo:** Provisionamento programático/administrativo.
- **Fluxo principal:** `POST /tenants` → `TenantService.create_tenant`.
- **Entradas:** tenant header + bearer; body `{id,name}`.
- **Saídas:** `{id,name}`.
- **Regras de negócio:** conflito se já existir.
- **Módulos/arquivos envolvidos:** `app/http/routes/tenants.py`, `modules/tenants/service/tenant_service.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** autorização granular inexistente (quem pode criar tenant?).

---

## F10 — Billing: catálogo de planos + limites + gates

- **Descrição:** Define tiers e limites; aplica gates para features (WhatsApp/Automations) e check de limites (users/customers/automations).
- **Objetivo:** Controle de capacidade e monetização.
- **Fluxo principal:**
  - `check_limit()` chamado em `AuthService.register` e `CrmService.create_customer`.
  - `can_use_feature(WHATSAPP)` usado no inbound webhook worker.
- **Entradas:** tenant context + operações do produto.
- **Saídas:** `GateResult`, `PlanStatus`, subscription atual.
- **Regras de negócio:** Starter restringe users/customers e desabilita WhatsApp.
- **Módulos/arquivos envolvidos:** `modules/billing/*`, `modules/iam/service/auth_service.py`, `modules/crm/service/crm_service.py`, `modules/messaging/service/inbound_webhook_service.py`.
- **Dependências externas:** N/A (mas requer persistência adequada).
- **Riscos, limitações e dúvidas:** persistência in-memory causa inconsistência API/worker.

---

## F11 — Billing API: status e set plan

- **Descrição:** Endpoints para consultar status e alterar tier do tenant.
- **Objetivo:** Operação/controle de plano (MVP/admin).
- **Fluxo principal:**
  - `GET /billing/status` → `BillingService.plan_status()`
  - `POST /billing/plan` → `BillingService.set_plan()`
- **Entradas:** tenant header + bearer; body `{tier}`.
- **Saídas:** JSON com status/subscription.
- **Regras de negócio:** depende do tenant context.
- **Módulos/arquivos envolvidos:** `app/http/routes/billing.py`, `modules/billing/service/billing_service.py`.
- **Dependências externas:** N/A.
- **Riscos, limitações e dúvidas:** sem RBAC; persistência in-memory.

---

## F12 — CRM: Customers (CRUD + listagem + soft delete/restore)

- **Descrição:** Gestão de clientes com paginação, busca e estágio de pipeline; suporta soft delete e restore.
- **Objetivo:** Base de dados de clientes do tenant.
- **Fluxo principal (API):**
  - `POST /crm/customers`
  - `GET /crm/customers` (page/page_size/query/search/stage/sort/order)
  - `GET /crm/customers/{id}`
  - `PATCH|PUT /crm/customers/{id}`
  - `DELETE /crm/customers/{id}`
  - `POST /crm/customers/{id}/restore`
- **Entradas:** payload do cliente e parâmetros de listagem.
- **Saídas:** customer em JSON e listas paginadas.
- **Regras de negócio:** limite de customers por plano; validações de sort/order no repo; soft delete.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/crm/service/crm_service.py`, `modules/crm/repo/sql.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** unicity de phone/email depende do schema no Postgres; validar consistência em sqlite.

---

## F13 — CRM: Interactions (criar e listar)

- **Descrição:** Histórico de interações por customer (ex.: notas e WhatsApp).
- **Objetivo:** Timeline e retenção/engajamento.
- **Fluxo principal:**
  - `POST /crm/customers/{id}/interactions`
  - `GET /crm/customers/{id}/interactions` (paginado, query, sort/order)
- **Entradas:** `{type,content}` e params.
- **Saídas:** interação criada e lista paginada.
- **Regras de negócio:** customer deve existir no tenant; busca/ordenação validadas no repo.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/crm/service/crm_service.py`, `modules/crm/repo/sql.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** modelo persiste `payload` JSON no ORM; consistência do mapeamento “content” deve ser garantida.

---

## F14 — CRM: Pipeline (movimentação de stage)

- **Descrição:** Move estágio do customer.
- **Objetivo:** Funil simples lead → booked → completed.
- **Fluxo principal:** `POST /crm/customers/{id}/stage`.
- **Entradas:** `{to_stage}`.
- **Saídas:** `{id, stage}`.
- **Regras de negócio:** transições permitidas são estritas.
- **Módulos/arquivos envolvidos:** `modules/crm/service/crm_service.py`, `app/http/routes/crm.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** sem estados “lost”/“paused”; regras podem precisar evoluir.

---

## F15 — Tenant Settings (CRUD parcial via CRM settings)

- **Descrição:** Leitura/atualização de preferências do tenant (timezone, currency, view, branding, default location).
- **Objetivo:** Configuração do workspace.
- **Fluxo principal:**
  - `GET /crm/settings` (get_or_create)
  - `PUT /crm/settings` (patch normalizado e validado)
- **Entradas:** patch de settings.
- **Saídas:** `TenantSettingsOut`.
- **Regras de negócio:** valida timezone IANA; currency upper; calendar view ∈ {week,day}; resolve/valida default location.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/tenants/repo/settings_sql.py`, `modules/tenants/models/tenant_settings_orm.py`.
- **Dependências externas:** DB, `zoneinfo`.
- **Riscos, limitações e dúvidas:** default `currency=USD` é fixo; requisitos regionais precisam confirmação.

---

## F16 — Locations (CRUD + listagem + default)

- **Descrição:** Gestão de unidades/locais do tenant, incluindo `default location`.
- **Objetivo:** Suportar agenda multi-unidade e settings.
- **Fluxo principal:**
  - `GET /crm/locations` (include_inactive/include_deleted)
  - `GET /crm/locations/default` (ensure_default_location + sincroniza settings)
  - `POST /crm/locations`
  - `GET/PUT/DELETE /crm/locations/{id}`
- **Entradas:** payload location, flags de listagem.
- **Saídas:** `LocationOut`, `LocationListOut`, `LocationDefaultOut`.
- **Regras de negócio:** soft delete marca `is_active=false` e seta `deleted_at`.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/crm/repo_locations.py`, `modules/tenants/repo/settings_sql.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** política do “default” (primeiro criado) pode ser insuficiente; validar necessidade de múltiplos defaults por contextos.

---

## F17 — Services (CRUD + listagem + soft delete/restore)

- **Descrição:** Catálogo de serviços (nome/preço/duração/ativo).
- **Objetivo:** Base para appointments e analytics.
- **Fluxo principal:**
  - `GET /crm/services` (paginado + query + include_inactive + sort/order)
  - `POST /crm/services` (campos obrigatórios)
  - `PATCH /crm/services/{id}` (patch)
  - `DELETE /crm/services/{id}` e `POST /restore`
- **Entradas:** payload do service e query params.
- **Saídas:** `ServiceOut`/`ServiceListOut`.
- **Regras de negócio:** valida sort/order; soft delete; criação exige campos.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/crm/repo_services.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** “service ativo” afeta criação de appointments; validar regra de negócio.

---

## F18 — Appointments (agenda) + prevenção de overlap + calendar view

- **Descrição:** CRUD de appointments com janelas de tempo, status, notas e política de conflitos por location.
- **Objetivo:** Agenda operacional.
- **Fluxo principal:**
  - `GET /crm/appointments` (filtros por range/ids/status, paginado)
  - `GET /crm/calendar` (join customer/service)
  - `POST /crm/appointments` (409 `APPOINTMENT_OVERLAP` em conflito)
  - `PATCH /crm/appointments/{id}`
  - `DELETE /crm/appointments/{id}` e `POST /restore`
- **Entradas:** payload appointment, parâmetros `from_dt/to_dt`.
- **Saídas:** `AppointmentOut`, `AppointmentListOut`, `CalendarOut` ou erro 409 com `conflicts`.
- **Regras de negócio:** from < to; valida UUIDs; location ativa e “overlaps” respeitado.
- **Módulos/arquivos envolvidos:** `app/http/routes/crm.py`, `modules/crm/repo_appointments.py`, `modules/crm/repo_locations.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** timezone é responsabilidade do cliente (envio ISO); status permitido é conjunto fechado.

---

## F19 — Analytics (sumário e métricas operacionais)

- **Descrição:** Endpoints para métricas: summary, overview, serviços, heatmap, bookings_over_time, at_risk.
- **Objetivo:** Dashboards e insights operacionais.
- **Fluxo principal:** cada endpoint agrega dados de appointments/customers/services no período e retorna JSON.
- **Entradas:** intervalos `from/to` (datetime), `location_id`, `threshold_days`; summary usa strings ISO.
- **Saídas:** JSON de métricas e listas.
- **Regras de negócio:** range válido; timezone do tenant (fallback UTC); `threshold_days` 1..365 e limite 200 itens no at_risk.
- **Módulos/arquivos envolvidos:** `app/http/routes/analytics.py`, `modules/analytics/service/analytics_service.py`, `modules/tenants/repo/settings_sql.py`.
- **Dependências externas:** DB, `zoneinfo`.
- **Riscos, limitações e dúvidas:** parte agrega em Python carregando muitos registros; avaliar performance para tenants grandes.

---

## F20 — Messaging: cadastro de WhatsApp account

- **Descrição:** Cria mapeamento `(provider, phone_number_id) -> tenant` com status.
- **Objetivo:** Roteamento correto de inbound webhooks.
- **Fluxo principal:** `POST /messaging/whatsapp-accounts`.
- **Entradas:** payload `{provider, phone_number_id, status}` + auth.
- **Saídas:** JSON da conta.
- **Regras de negócio:** unicidade por `(provider, phone_number_id)`.
- **Módulos/arquivos envolvidos:** `app/http/routes/messaging.py`, migrations em `alembic/versions/0e7c0b3f3b9c_add_messaging_tables_and_rls.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** precisa de RBAC; impacto de RLS no lookup inbound deve ser validado.

---

## F21 — Messaging: inbound webhook (validação, queue, idempotência e persistência)

- **Descrição:** Recebe inbound, valida assinatura, resolve tenant, enfileira Celery e processa com dedupe.
- **Objetivo:** Ingestão segura e escalável de mensagens inbound (WhatsApp).
- **Fluxo principal (HTTP):**
  1) `POST /messaging/inbound` valida `X-Hub-Signature-256`.
  2) Busca WhatsApp account por provider/phone_number_id.
  3) Enfileira `enqueue_inbound_webhook(...)` e retorna `accepted`.
- **Fluxo principal (worker):**
  1) Seta tenant context baseado na conta.
  2) Verifica gate do plano (WhatsApp).
  3) Registra `webhook_event` com unique (idempotência).
  4) Upsert conversation; cria message; cria interaction no CRM; marca evento `processed`.
- **Entradas:** payload inbound, assinatura, Redis/Celery.
- **Saídas:** HTTP `{status:"accepted"}`; processamento `{status:"processed"|"duplicate"}`.
- **Regras de negócio:** assinatura obrigatória; não confiar em `X-Tenant-ID` no webhook; WhatsApp precisa estar no plano.
- **Módulos/arquivos envolvidos:** `app/http/routes/messaging.py`, `tasks/queue.py`, `tasks/workers/messaging/inbound_worker.py`, `modules/messaging/service/inbound_webhook_service.py`, `modules/messaging/repo/sql.py`.
- **Dependências externas:** Meta/WhatsApp (assinatura), Redis, Celery, DB.
- **Riscos, limitações e dúvidas:** sem auto-criação de customer (falha se não existir); infraestrutura local de Redis/worker não está definida em compose.

---

## F22 — Queue/Worker: retry/backoff e DLQ (dead_letter)

- **Descrição:** Celery task com retry; em falha persistente marca `webhook_events` como `dead_letter`.
- **Objetivo:** Resiliência e rastreabilidade de falhas de processamento.
- **Fluxo principal:**
  1) Task configurada com `autoretry_for`, `retry_backoff`, `max_retries=5`.
  2) `on_failure` resolve conta e marca status `dead_letter`.
- **Entradas:** payload do webhook, conectividade com DB e Redis.
- **Saídas:** status atualizado em `webhook_events`.
- **Regras de negócio:** em test/`CELERY_TASK_ALWAYS_EAGER`, tasks rodam eager.
- **Módulos/arquivos envolvidos:** `tasks/queue.py`, `modules/messaging/repo/sql.py`.
- **Dependências externas:** Celery, Redis, DB.
- **Riscos, limitações e dúvidas:** ausência de métricas/alertas para DLQ; compose não define Redis.

---

## F23 — Auditoria: audit_log (before/after) e soft delete

- **Descrição:** Registra ações (created/updated/deleted/status_changed) com snapshot JSON e user_id do contexto.
- **Objetivo:** Compliance e rastreabilidade.
- **Fluxo principal:**
  1) Repos capturam `before`/`after` via `snapshot_orm()`.
  2) `record_audit_log()` grava linha em `audit_log`.
- **Entradas:** sessão DB, `tenant_id`, ação, entidade, snapshots.
- **Saídas:** registros em `audit_log`.
- **Regras de negócio:** normalização JSON-safe de tipos (UUID, datetime, Enum, Decimal).
- **Módulos/arquivos envolvidos:** `modules/audit/logging.py`, `modules/audit/models/audit_log_orm.py`, repos em `modules/crm/*`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** cobertura depende de repos chamarem auditoria; não há auditoria explícita de eventos de auth/admin.

---

## F24 — Seed demo (script CLI)

- **Descrição:** Cria tenant demo, user, token, customer e whatsapp account, e imprime valores.
- **Objetivo:** Facilitar testes manuais e demo.
- **Fluxo principal:** executa `tasks/seed_demo.py` com `SEED_*` envs.
- **Entradas:** env vars e acesso ao DB.
- **Saídas:** prints (tenant/user/token/ids).
- **Regras de negócio:** respeita limits do billing indiretamente (pode falhar).
- **Módulos/arquivos envolvidos:** `tasks/seed_demo.py`.
- **Dependências externas:** DB.
- **Riscos, limitações e dúvidas:** imprime segredo/token; recomendado apenas para dev.

---

## F25 — Frontend: sessão, login, register, logout e proteção de rotas

- **Descrição:** Next.js com páginas `/login`, `/register`, `/logout` e proteção de `/dashboard/*`.
- **Objetivo:** UI base do CRM.
- **Fluxo principal:**
  - `/register` → chama `/auth/signup` e salva `token/tenant_id`.
  - `/login` → chama `/auth/login_email`; se necessário, seleciona workspace via `/auth/select_workspace`.
  - Middleware Next redireciona para login se cookies ausentes.
  - Logout limpa storage/cookies.
- **Entradas:** credenciais e respostas da API; cookies/localStorage.
- **Saídas:** navegação e sessão no browser.
- **Regras de negócio:** 401 no axios interceptor → limpa auth e redireciona login.
- **Módulos/arquivos envolvidos:** `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx`, `frontend/app/logout/page.tsx`, `frontend/middleware.ts`, `frontend/lib/auth.ts`.
- **Dependências externas:** Next.js, React, Axios.
- **Riscos, limitações e dúvidas:** token em localStorage/cookie não-HttpOnly aumenta exposição a XSS; avaliar hardening.

---

## F26 — Frontend: client HTTP (Axios) + headers + parsing de erros

- **Descrição:** Axios injeta `Authorization` e `X-Tenant-ID`; parseia erros do backend, incluindo conflitos de appointment.
- **Objetivo:** Consumo consistente da API e UX melhor.
- **Fluxo principal:** interceptors request/response + `parseApiError()`.
- **Entradas:** `NEXT_PUBLIC_API_BASE_URL`, token/tenant, payloads de erro.
- **Saídas:** erros normalizados para UI e eventos `app:api-error`.
- **Regras de negócio:** trata `APPOINTMENT_OVERLAP` como conflito; extrai `details.fields`.
- **Módulos/arquivos envolvidos:** `frontend/lib/api.ts`, `frontend/lib/api-errors.ts`.
- **Dependências externas:** Axios.
- **Riscos, limitações e dúvidas:** contrato de erro precisa permanecer compatível; mudanças no backend podem quebrar parsing.

---

## F27 — Frontend: Default Location Provider

- **Descrição:** Provider React que carrega `GET /crm/locations/default` e fornece a location padrão no dashboard.
- **Objetivo:** Evitar duplicação de chamadas e padronizar contexto de agenda.
- **Fluxo principal:** ao montar, chama API e mantém `defaultLocation` em contexto; expõe `refresh()`.
- **Entradas:** sessão autenticada.
- **Saídas:** contexto React.
- **Regras de negócio:** N/A (cliente).
- **Módulos/arquivos envolvidos:** `frontend/lib/default-location.tsx`, `frontend/app/dashboard/layout.tsx`.
- **Dependências externas:** React, Axios.
- **Riscos, limitações e dúvidas:** falhas na API degradam UX; ausência de fallback.
