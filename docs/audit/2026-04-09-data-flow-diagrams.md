# Data Flow Diagrams — Core Workflows (Beauty CRM)

Data: **2026-04-09**  
Audience: **Engenharia / Produto / Ops**

> Diagramas em Mermaid para facilitar revisão e onboarding.

## 1) Authenticated dashboard request (tenant-scoped)

```mermaid
sequenceDiagram
  autonumber
  participant Browser as Browser (Next.js)
  participant API as API (FastAPI)
  participant MW as Tenancy middleware
  participant Deps as Auth deps (require_user)
  participant DB as DB (Postgres/SQLite)

  Browser->>API: GET /crm/customers + X-Tenant-ID + Bearer token
  API->>MW: tenancy_middleware
  MW->>MW: set_tenant_id(tenant_id)
  API->>Deps: require_user()
  Deps->>Deps: verify_token() + tenant_mismatch check
  API->>DB: db_session() (set_config app.current_tenant_id)
  DB-->>API: tenant-scoped rows (RLS and/or filters)
  API-->>Browser: 200 OK (data)
  MW->>MW: clear_tenant_id(); clear_current_user_id()
```

## 2) Signup flow (new workspace)

```mermaid
sequenceDiagram
  autonumber
  participant Browser as Browser (Next.js)
  participant API as API (FastAPI)
  participant Auth as /auth/signup
  participant DB as DB

  Browser->>API: POST /auth/signup (tenant_name, email, password)
  API->>Auth: signup()
  Auth->>Auth: generate tenant_id (UUID)
  Auth->>Auth: set_tenant_id(tenant_id) BEFORE db_session
  Auth->>DB: db_session() + create tenant + create user
  Auth->>DB: ensure default location (+ tenant_settings default_location)
  DB-->>Auth: persisted rows
  Auth-->>Browser: 200 OK (tenant_id, token)
  Browser->>Browser: persist token + tenant_id
  Browser->>API: subsequent authenticated requests (tenant-scoped)
```

## 3) Inbound WhatsApp webhook (signature → routing → queue → processing)

```mermaid
sequenceDiagram
  autonumber
  participant Provider as WhatsApp/Meta
  participant API as API (FastAPI)
  participant Repo as MessagingRepo
  participant Q as Celery/Redis
  participant Worker as Celery Worker
  participant DB as DB

  Provider->>API: POST /messaging/inbound (payload + X-Hub-Signature-256)
  API->>API: verify_signature(body, secret)
  alt invalid signature
    API-->>Provider: 401 invalid_signature
  else valid signature
    API->>Repo: get_whatsapp_account(provider, phone_number_id)
    alt account not found
      API-->>Provider: 404 whatsapp_account_not_found
    else account found
      API->>Q: enqueue_inbound_webhook(payload, signature_valid=true)
      API-->>Provider: 200 {status:"accepted"}
      Worker->>Q: consume task
      Worker->>Repo: record_webhook_event (idempotency)
      alt duplicate external_event_id
        Worker-->>Q: {status:"duplicate"}
      else new event
        Worker->>DB: upsert conversation + insert message
        Worker->>DB: add CRM interaction
        Worker->>Repo: mark_webhook_event_status(processed)
        Worker-->>Q: {status:"processed"}
      end
    end
  end
```

### Failure path: retries and DLQ

```mermaid
sequenceDiagram
  autonumber
  participant Worker as Celery Worker
  participant Q as Celery/Redis
  participant Repo as MessagingRepo
  participant DB as DB

  Worker->>Q: execute inbound task
  alt transient failure
    Worker-->>Q: retry (backoff)
  else persistent failure (max retries exceeded)
    Worker->>Repo: mark_webhook_event_status(dead_letter)
    Repo->>DB: UPDATE webhook_events SET status='dead_letter'
  end
```

## 4) Notes (assumptions and validations)

- O fluxo inbound assume que o lookup de `whatsapp_accounts` é possível sem tenant context; isso precisa ser validado sob RLS (ver auditoria).
- Em ambiente local, é necessário Redis + worker rodando para simular produção (compose atual não inclui).

