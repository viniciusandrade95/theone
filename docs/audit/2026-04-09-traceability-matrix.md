# Traceability Matrix — Features ↔ Code ↔ Data ↔ Tests (Beauty CRM)

Data: **2026-04-09**  
Audience: **Engenharia / QA / Security**

Objetivo: para cada feature, mapear **rotas**, **serviços**, **repos**, **tabelas/entidades** e **testes** observados.

Legenda “Confiança”:
- **Confirmado:** evidência direta no código
- **Inferido:** conclusão provável por estrutura/nomes
- **Precisa validação:** depende de runtime/ambiente (ex.: RLS em Postgres)

> Nota: para detalhes de comportamento, ver `docs/audit/2026-04-09-functional-catalog.md`.

## Matriz (core)

| Feature ID | Feature (user-facing) | Rotas / UI | Services | Repos | Tabelas/Entidades | Testes | Confiança |
|---|---|---|---|---|---|---|---|
| F01 | API bootstrap + CORS + routers | ASGI `main.py`; app factory `app/http/main.py` | Container (wiring) | N/A | N/A | `tests/api/test_smoke_api.py` (cria app), `tests/api/test_cors_preflight.py` | Confirmado |
| F02 | Contrato de erros HTTP (normalização) | Handlers globais | N/A | N/A | N/A | `tests/api/test_error_normalization_api.py`, `tests/unit/test_errors.py` | Confirmado |
| F03 | Tenancy por header + ContextVar | middleware em `app/http/main.py` | N/A | N/A | N/A | `tests/unit/test_tenancy.py`, `tests/api/test_tenant_isolation.py` | Confirmado |
| F04 | DB session + tenant context (set_config) | `core/db/session.py` | N/A | N/A | N/A | `tests/integration/test_signup_rls_postgress.py` (RLS), `tests/unit/test_tenant_isolation_repo.py` | Confirmado (RLS: Precisa validação) |
| F05 | Tokens (HMAC) + preauth | `app/auth_tokens.py`; rotas auth | N/A | N/A | N/A | `tests/api/test_tenant_isolation.py` (tenant_mismatch), `tests/api/test_auth_me.py` | Confirmado |
| F06 | Onboarding: criar workspace + primeiro user | `POST /auth/signup`; UI `frontend/app/register/page.tsx` | `AuthService` | `SqlTenantRepo`, `SqlUserRepo`, `LocationsRepo`, `SqlTenantSettingsRepo` | `tenants`, `users`, `locations`, `tenant_settings` | `tests/api/test_signup.py`, `tests/integration/test_signup_rls_postgress.py` | Confirmado (runtime RLS: Precisa validação) |
| F08 | Login global + seleção de workspace | `POST /auth/login_email`, `POST /auth/select_workspace`; UI `frontend/app/login/page.tsx` | `AuthService` (parcial) | `SqlUserRepo`, `SqlTenantRepo` | `users`, `tenants` | `tests/api/test_signup.py` (parcial), `tests/api/test_auth_me.py` (parcial) | Confirmado |
| F07 | Login por tenant + `/me` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | `AuthService` | `SqlUserRepo` | `users` | `tests/api/test_auth_me.py`, `tests/api/test_smoke_api.py` | Confirmado |
| F12 | Manage customer records | `/crm/customers*`; UI (inferido) | `CrmService` | `SqlCrmRepo` | `customers` | `tests/api/test_customers_api.py`, `tests/api/test_tenant_isolation.py` | Confirmado |
| F13 | Customer interactions timeline | `/crm/customers/{id}/interactions` | `CrmService` | `SqlCrmRepo` | `interactions` | `tests/api/test_services_appointments_api.py` (interactions) | Confirmado |
| F14 | Pipeline stage transitions | `/crm/customers/{id}/stage` | `CrmService` | `SqlCrmRepo` | `customers` | (parcial) `tests/api/test_customers_api.py` | Inferido/Confirmado |
| F16 | Workspace settings | `/crm/settings` | (repo-centric) | `SqlTenantSettingsRepo` | `tenant_settings`, `locations` | `tests/api/test_tenant_settings_api.py` | Confirmado |
| F18 | Scheduling (appointments + calendar) | `/crm/appointments`, `/crm/calendar`; UI (inferido) | (repo-centric) | `AppointmentsRepo` | `appointments`, `customers`, `services`, `locations` | `tests/api/test_services_appointments_api.py`, `tests/api/test_audit_soft_delete_api.py` | Confirmado |
| F17 | Services catalog | `/crm/services*` | (repo-centric) | `ServicesRepo` | `services` | `tests/api/test_services_appointments_api.py` | Confirmado |
| F18b | Overlap prevention | `POST /crm/appointments` (409) | (repo-centric) | `AppointmentsRepo` | `appointments`, `locations` | `tests/api/test_services_appointments_api.py` | Confirmado |
| F19 | Analytics dashboards | `/analytics/*` | `AnalyticsService` (summary) | `SqlAnalyticsRepo` (summary), SQL in router (others) | `appointments`, `customers`, `services`, `tenant_settings` | `tests/api/test_analytics_api.py`, `tests/api/test_smoke_api.py` | Confirmado |
| F20 | WhatsApp account mapping | `POST /messaging/whatsapp-accounts` | N/A | `SqlMessagingRepo` | `whatsapp_accounts` | (parcial) `tests/api/test_inbound_webhook.py` setup | Confirmado |
| F21 | Inbound WhatsApp webhook | `POST /messaging/inbound` | `InboundWebhookService` | `SqlMessagingRepo` | `whatsapp_accounts`, `webhook_events`, `conversations`, `messages`, `interactions` | `tests/api/test_inbound_webhook.py`, `tests/unit/test_events_and_worker.py` | Confirmado (RLS routing: Precisa validação) |
| F22 | Queue + retry + DLQ | `tasks/queue.py` | `InboundWebhookService` | `SqlMessagingRepo` | `webhook_events` | `tests/api/test_inbound_webhook.py` (eager), `tests/unit/test_events_and_worker.py` | Confirmado |
| F23 | Audit log | (indireto) | N/A | repos CRM + `record_audit_log` | `audit_log` | `tests/api/test_audit_soft_delete_api.py` | Confirmado |
| F11 | Billing status / set plan | `/billing/status`, `/billing/plan` | `BillingService` | `InMemoryBillingRepo` | (sem tabela) | `modules/billing/tests/test_plan_status.py` | Confirmado |
| F24 | Seed demo (CLI) | `tasks/seed_demo.py` | `AuthService` | repos SQL + messaging repo | `tenants`, `users`, `customers`, `whatsapp_accounts` | (não observado) | Confirmado |
| F25 | Frontend session + route protection | UI `/login`, `/register`, `/dashboard/*` | N/A | N/A | cookies/localStorage | (não observado) | Confirmado |
| F26 | Frontend API client + error parsing | `frontend/lib/api.ts`, `frontend/lib/api-errors.ts` | N/A | N/A | N/A | (não observado) | Confirmado |
| F27 | Frontend default location context | `frontend/lib/default-location.tsx` | N/A | N/A | `locations` (via API) | (não observado) | Confirmado |

## Gap notes (para completar a matriz)

- UI de dashboard (customers/services/appointments) tem componentes e navegação parcial; mapear rotas Next completas exige leitura de `frontend/app/dashboard/*` (fora do escopo desta matriz “core”).
- Cobertura de RLS em Postgres precisa validação em runtime (há testes de integração, mas dependem de ambiente Postgres corretamente migrado).
