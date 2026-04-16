# Auditoria Técnica — Projeto Python (Beauty CRM)

Data: **2026-04-09**  
Autor: Staff Engineer (auditoria técnica)  
Escopo: **backend (FastAPI + SQLAlchemy + Alembic + Celery)** e **frontend (Next.js)** no repositório.

## 0) Atualizações pós-auditoria (2026-04-16)

Este documento foi escrito em **2026-04-09**. Em **2026-04-16**, um PR de hardening foi aplicado para reduzir os principais riscos de operação do WhatsApp em produção, mantendo mudanças **incrementais**:

- **C1 (segredos versionados):** `.env` foi removido do repositório e `.gitignore` passou a ignorar `.env` (e variações), reduzindo o risco de novo vazamento. **Atenção:** as credenciais previamente expostas **devem ser rotacionadas** imediatamente.
- **C2 (billing in-memory):** billing passou a ser persistido via tabela `billing_subscriptions` + `SqlBillingRepo`, eliminando inconsistência entre processos (API vs Celery worker) para gates de WhatsApp.
- **C3 (RLS em whatsapp_accounts):** RLS foi **desabilitado** em `whatsapp_accounts` (tabela de roteamento `provider + phone_number_id -> tenant_id`) para permitir resolução de tenant em callbacks provider-driven antes de existir contexto de tenant.
- **A1 (RBAC):** foi adicionado um RBAC mínimo e conservador para rotas sensíveis (billing/tenants/whatsapp-accounts): **admin = primeiro usuário criado do tenant**. Isto é um guardrail temporário até existir modelo de roles/memberships.
- **A2 (observabilidade):** a auditoria indicava arquivos vazios; atualmente existe baseline funcional de **logs estruturados**, **métricas em memória** e **trace id**. Foram adicionados contadores específicos para rejeições/aceites do webhook (assinatura, verify token, unknown routing).

O restante do documento permanece válido como diagnóstico e backlog; os itens acima foram os focos de mitigação imediata.

## 1) Contexto e metodologia

Esta auditoria foi baseada em leitura estática do código e artefatos do repositório (estrutura, rotas, serviços, repos, migrations, testes e frontend).  
**Não inclui** validação em ambiente de produção nem execução completa da suíte de testes em um ambiente isolado (ver achado de testabilidade).

Critérios analisados:
- Estrutura do projeto
- Qualidade de código
- Acoplamento e coesão
- Tratamento de erros
- Observabilidade
- Segurança
- Testabilidade
- Escalabilidade
- Dívida técnica

## 1.1 Leitura recomendada (stakeholders vs engenharia)

- **Stakeholders (exec/PM/security):** `docs/audit/2026-04-09-project-assessment-executive-summary-risk-register-roadmap.md`
- **Engenharia (auditoria detalhada):** este documento
- **Arquitetura/fluxos:** `docs/audit/2026-04-09-system-purpose-architecture.md` e `docs/audit/2026-04-09-data-flow-diagrams.md`
- **Funcionalidades e rastreabilidade:** `docs/audit/2026-04-09-functional-catalog.md` e `docs/audit/2026-04-09-traceability-matrix.md`

## 2) Visão geral da arquitetura (alto nível)

- **Monólito modular por domínio** (`modules/*`) com infraestrutura transversal em `core/*` e interface HTTP em `app/http/*`.
- **Tenancy** via header + ContextVar + (opcional) **RLS** no Postgres usando `set_config('app.current_tenant_id', ...)`.
- **Mensageria inbound (WhatsApp)**: rota pública valida assinatura, resolve tenant e enfileira processamento via **Celery + Redis**; worker persiste `webhook_events`, `conversations`, `messages` e cria interação no CRM.
- **Frontend** em Next.js com axios e proteção de rotas `/dashboard/*`.

Principais entrypoints:
- API ASGI: `main.py` (compatibilidade), `app/http/main.py` (factory + routers)
- Worker queue: `tasks/queue.py`

## 3) Sumário executivo (principais riscos)

Há **3 riscos críticos** que podem quebrar produção ou expor dados/infra:
1) **Segredos/credenciais versionados** no repositório (`.env`).
2) **Billing in-memory** gera inconsistência entre processos (API vs Celery worker) e perda de estado.
3) **RLS em `whatsapp_accounts`** (policy dependente de `current_setting('app.current_tenant_id')`) conflita com o fluxo de inbound webhook que precisa resolver tenant **antes** de existir contexto de tenant.

### 3.1 Deployment blockers (interpretação operacional)

Os itens **C1/C2/C3** devem ser tratados como **bloqueadores de deploy/escala**, porque:
- C1: risco imediato de incidente de segurança e acesso indevido a dados.
- C2: torna o produto não determinístico quando API e worker estão separados (cenário padrão em produção).
- C3: pode derrubar o canal inbound de WhatsApp quando RLS está ativo (cenário esperado para multi-tenant “hard isolation”).

## 4) Achados por severidade

### 4.1 Crítico

#### C1) Segredos/credenciais versionados no repositório

- **Evidência:**
  - `.env` contém `DATABASE_URL` com credenciais e host remoto.
- **Impacto:**
  - Exposição de acesso ao banco/ambiente (risco de exfiltração/alteração de dados, custos e incidente de segurança).
  - Incentivo ao uso indevido de `.env` em produção.
- **Recomendação:**
  - Remover `.env` do controle de versão e adicionar ao `.gitignore`.
  - Rotacionar imediatamente credenciais expostas.
  - Usar `.env.example` como contrato e um gerenciador de segredos (Vault/SSM/GitHub Actions Secrets).
- **Prioridade:** **P0 (imediato)**.

---

#### C2) Billing in-memory: inconsistência entre processos (API vs worker) e perda de estado

- **Evidência:**
  - Container usa `InMemoryBillingRepo`: `app/container.py:38`.
  - Repo é dicionário em memória: `modules/billing/repo/in_memory.py:5`.
  - Worker cria container novo por execução/task: `tasks/queue.py:58`.
  - Endpoint altera plano (apenas no processo atual): `app/http/routes/billing.py:30`.
- **Impacto:**
  - Em produção, **API e worker são processos distintos**; o worker não observa o plano alterado pela API.
  - Gates de feature (ex.: WhatsApp) tornam-se não determinísticos; reinício/escala horizontal “reseta” subscriptions.
- **Recomendação:**
  - Implementar `SqlBillingRepo` (tabelas de subscription/entitlements) e usar o mesmo storage no container do API e do worker.
  - Adicionar migração e testes de integração para garantir consistência entre processos.
- **Prioridade:** **P0**.

---

#### C3) RLS em `whatsapp_accounts` inviabiliza resolução de tenant no inbound webhook

- **Evidência:**
  - Rota inbound bypassa tenancy middleware: `app/http/main.py:99`.
  - Antes de setar tenant, rota consulta `whatsapp_accounts`: `app/http/routes/messaging.py:40`.
  - Migração habilita RLS e policy depende de `current_setting('app.current_tenant_id')`: `alembic/versions/0e7c0b3f3b9c_add_messaging_tables_and_rls.py:126` e `alembic/versions/0e7c0b3f3b9c_add_messaging_tables_and_rls.py:140`.
  - Query do repo não filtra por tenant (por design do lookup): `modules/messaging/repo/sql.py:23`.
- **Impacto:**
  - Com RLS ativo, `SELECT` pode retornar 0 linhas (ou falhar) quando `app.current_tenant_id` não está setado.
  - Resultado: webhooks inbound ficam indisponíveis em Postgres com RLS.
- **Recomendação (escolher e padronizar):**
  - **Opção A:** desabilitar RLS apenas em `whatsapp_accounts` (tabela de roteamento).
  - **Opção B:** manter RLS mas prover mecanismo de lookup seguro (função `SECURITY DEFINER`/view controlada) para resolver tenant sem contexto.
  - Ajustar policies para `current_setting('app.current_tenant_id', true)` onde apropriado e adicionar testes específicos de webhook + RLS.
- **Prioridade:** **P0**.

---

### 4.2 Alto

#### A1) Falta de autorização (RBAC/permissões) para ações sensíveis

- **Evidência:**
  - Módulos de permissões vazios (stubs): `core/security/permissions.py` e `core/security/auth.py` (0 bytes).
  - Qualquer usuário autenticado pode alterar plano: `app/http/routes/billing.py:30`.
  - Qualquer usuário autenticado pode criar tenant arbitrário: `app/http/routes/tenants.py:15`.
- **Impacto:**
  - Elevação de privilégio “por design”; conta comprometida pode alterar billing e provisionar tenants.
  - Dificulta governança enterprise.
- **Recomendação:**
  - Implementar RBAC mínimo (roles/memberships) e checagem por rota (`billing:write`, `tenants:provision`).
  - Adicionar testes de autorização.
- **Prioridade:** **P1**.

---

#### A2) Observabilidade inexistente

- **Evidência (2026-04-09):**
  - Em 2026-04-09, a observabilidade estava ausente/insuficiente.
- **Status (2026-04-16):**
  - Existe baseline funcional em `core/observability/*` e middleware HTTP instrumenta requests.
  - Fluxos de WhatsApp ganharam contadores/logs mínimos (aceite/rejeição/unknown routing) para operação inicial.
- **Impacto:**
  - Operação arriscada: sem rastreabilidade de requests/tasks, difícil identificar falhas e investigar incidentes.
- **Recomendação:**
  - Logging estruturado (request_id/tenant_id/user_id), métricas (latência, erro, DLQ) e tracing.
  - Correlation id propagado API → Celery.
- **Prioridade:** **P1**.

---

#### A3) Enforcements de tenancy incompletos no middleware (existência do tenant comentada)

- **Evidência:**
  - Checagem de existência do tenant está comentada: `app/http/main.py:118`.
- **Impacto:**
  - Permite tenant ids “inventados” via header; sujeira e inconsistência de provisionamento.
- **Recomendação:**
  - Reativar validação de tenant (com fast-path/caching) e separar claramente rotas públicas/provisioning.
- **Prioridade:** **P1**.

---

#### A4) Token HMAC custom (sem refresh/rotação/revogação)

- **Evidência:**
  - Implementação de token minimalista: `app/auth_tokens.py:33`.
- **Impacto:**
  - Revogação e rotação de chaves difíceis; limita integrações enterprise e incident response.
- **Recomendação:**
  - Migrar para JWT com `kid`, rotação de chaves; adicionar refresh token e/ou store de sessões.
- **Prioridade:** **P1**.

---

#### A5) Infra local incompleta para execução do pipeline async

- **Evidência:**
  - Celery depende de Redis (`REDIS_URL`): `core/config/env.py:52` e `tasks/queue.py:15`.
  - `docker-compose.yml` não inclui Redis/worker: `docker-compose.yml:1`.
  - Runbooks vazios: `docs/runbooks/local-dev.md` (0 bytes).
- **Impacto:**
  - Ambientes inconsistentes; maior custo de QA; falhas não reproduzíveis.
- **Recomendação:**
  - Completar compose com Redis + worker + variáveis e documentar passo-a-passo.
- **Prioridade:** **P1**.

---

### 4.3 Médio

#### M1) Testes não executam “out of the box” (ambiente não padronizado)

- **Evidência:**
  - Não há workflow padrão (sem `pyproject.toml`, `setup.py`, `tox.ini`, `Makefile`) e o repositório contém um `venv/` e `__pycache__/` (higiene de repo).
  - Em ambiente “limpo” sem instalação prévia, `pytest` falha na collection até que as dependências sejam instaladas (ex.: `httpx`, `sqlalchemy`), apesar de estarem listadas em `requirements.txt`.
- **Impacto:**
  - Menor confiança em regressões; onboarding lento; CI local difícil.
- **Recomendação:**
  - Definir workflow único (ex.: `uv`/Poetry/pip) e remover `venv/` do repo.
  - Preencher `README.md` com setup, `make test`, e pinagem de Python.
- **Prioridade:** **P2**.

---

#### M2) Header de tenant configurável vs hardcoded em deps/clients

- **Evidência:**
  - Middleware usa `TENANT_HEADER`: `app/http/main.py:105`.
  - Dependência OpenAPI exige `X-Tenant-ID`: `app/http/deps.py:49`.
  - Frontend injeta `X-Tenant-ID`: `frontend/lib/api.ts:32`.
- **Impacto:**
  - Mudança do header quebra clients/docs silenciosamente.
- **Recomendação:**
  - Padronizar: header invariável (remover config) ou refatorar deps/clients para respeitar config.
- **Prioridade:** **P2**.

---

#### M3) Analytics com agregações em Python (risco de memória/latência em tenants grandes)

- **Evidência:**
  - `heatmap` carrega lista de `starts_at` e agrega em memória: `app/http/routes/analytics.py:251`.
  - `bookings_over_time` idem: `app/http/routes/analytics.py:293`.
- **Impacto:**
  - Escala mal com volume; aumenta latência e uso de memória.
- **Recomendação:**
  - Mover agregação para SQL (GROUP BY) ou pré-aggregar via jobs.
- **Prioridade:** **P2**.

---

#### M4) Contagens ineficientes no repo de messaging

- **Evidência:**
  - `count_messages` e `count_webhook_events` fazem `SELECT` e `len(all())`: `modules/messaging/repo/sql.py:156`.
- **Impacto:**
  - Custo desnecessário e degrada com crescimento.
- **Recomendação:**
  - Trocar para `SELECT count(*)` e validar índices.
- **Prioridade:** **P3**.

---

#### M5) Mistura de camadas (rotas usam ORM/SQL direto e repos direto)

- **Evidência:**
  - CRM customers via service: `app/http/routes/crm.py:188`.
  - CRM services/appointments via repos direto: `app/http/routes/crm.py:663` e `app/http/routes/crm.py:824`.
  - Analytics com SQL direto no router: `app/http/routes/analytics.py:108`.
- **Impacto:**
  - Regras espalhadas; menor coesão; dificulta testes unitários e evolução.
- **Recomendação:**
  - Definir padrão (routers → services → repos) e aplicá-lo nas áreas críticas primeiro.
- **Prioridade:** **P3**.

---

#### M6) Drivers Postgres redundantes

- **Evidência:** coexistem `psycopg`, `psycopg-binary`, `psycopg2-binary`: `requirements.txt:29`, `requirements.txt:30`, `requirements.txt:31`.
- **Impacto:** conflitos e troubleshooting mais difícil.
- **Recomendação:** escolher um stack (preferência psycopg3) e padronizar `DATABASE_URL`.
- **Prioridade:** **P3**.

---

### 4.4 Baixo

#### B0) Higiene de repositório: artefatos versionados (`venv`, `__pycache__`, `.pyc`)

- **Evidência:**
  - Diretórios `venv/` e `__pycache__/` no repo; há `.pyc` dentro de `tests/api/__pycache__/` e `tests/integration/__pycache__/`.
- **Impacto:**
  - PRs ruidosos, maior chance de conflitos, risco de “state leakage” e confusão em onboarding.
- **Recomendação:**
  - Atualizar `.gitignore` (python + venv + build artifacts) e limpar artefatos do VCS.
- **Prioridade:** **P4**.

---

#### B1) Placeholders vazios (dívida e confusão arquitetural)

- **Evidência:** 0 bytes: `core/events/handlers.py`, `core/tenancy/middleware.py`, `tasks/schedulers/daily.py`, `tasks/schedulers/monthly.py`, etc.
- **Impacto:** ruído, confusão e falsa percepção de cobertura.
- **Recomendação:** remover arquivos não usados ou implementar mínimo funcional + docs.
- **Prioridade:** **P4**.

---

#### B2) Documentação essencial vazia

- **Evidência:** 0 bytes: `README.md`, `DECISIONS.md`, `PROJECT_RULES.md`, `docs/runbooks/local-dev.md`, `docs/runbooks/deployment.md`.
- **Impacto:** onboarding e operação deficientes.
- **Recomendação:** preencher com setup/test/deploy/runbooks e decisões arquiteturais.
- **Prioridade:** **P4**.

---

#### B3) Higiene de código (duplicações/format)

- **Evidência:** imports duplicados e redundâncias em `app/auth_tokens.py`.
- **Impacto:** baixo; mas indica ausência de lint/format automático.
- **Recomendação:** adotar formatter/linter (ex.: ruff) e CI mínimo.
- **Prioridade:** **P4**.

## 5) Próximos passos recomendados (ordem sugerida)

1) **P0**: remover `.env` do repo + rotação de credenciais + hardening de segredos.  
2) **P0**: persistir billing/subscriptions (eliminar `InMemoryBillingRepo`).  
3) **P0**: corrigir desenho de RLS/lookup do inbound webhook (`whatsapp_accounts`).  
4) **P1**: RBAC mínimo (bloquear `billing/plan`, `tenants` e outras ações administrativas).  
5) **P1**: observabilidade (logging estruturado + métricas + tracing).  
6) **P1/P2**: completar ambiente local (compose + runbooks) e padronizar execução de testes.  
7) **P2/P3**: otimizações de queries/contagens e padronização de camadas.

## 6) Security posture (checklist rápido)

> Este checklist não substitui uma threat model formal, mas explicita os gaps observados.

- **Segredos:** segredos não podem estar em VCS (ver C1).
- **Token/session:** token é HMAC custom (ver A4); frontend persiste token em `localStorage` e cookies não-HttpOnly (exposição a XSS) — requer decisão de produto/segurança.
- **Webhooks:** há validação de assinatura e idempotência (ponto positivo), mas precisa validação sob RLS e com rate limiting/WAF.
- **Autorização:** RBAC ausente (ver A1).
- **Least privilege:** confirmar permissões do usuário de DB e separação por ambientes (Precisa validação).
- **Dependências:** não há evidência de scanning (sem CI), nem lockfile; recomendar `pip-audit`/SCA em pipeline.

## 7) Testes e CI (estado atual)

- **Tipos de teste existentes (Confirmado):**
  - API tests: `tests/api/*`
  - Unit tests: `tests/unit/*` e `modules/*/tests/*`
  - Integration tests (Postgres/RLS): `tests/integration/*`
- **CI (Confirmado):**
  - Não há diretório `.github/workflows` nem outros manifests de CI no repo.
- **Recomendação:**
  - Introduzir CI mínimo (lint + unit + API tests) e um job “integration” com Postgres para validar RLS e fluxo de signup.
