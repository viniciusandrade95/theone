# Project Assessment — Executive Summary, Risk Register, and Roadmap (Beauty CRM)

Data: **2026-04-09**  
Audience: **Leadership / PM / Security / Engineering**  
Confidence model: cada afirmação é marcada como **Confirmado**, **Inferido** ou **Precisa validação**.

## 1) Executive summary (one page)

### O que é o produto (Confirmado)
- Um **CRM SaaS multi-tenant** voltado a “Beauty & Lifestyle”, implementado como **monólito modular por domínio** com API FastAPI + frontend Next.js. (ver `docs/architecture/repo-map.md` e `frontend/README.md`)

### Quem usa (Inferido)
- **Operação (frontline):** equipe de atendimento/receção (agenda e clientes).  
- **Gestão:** owner/manager (métricas e configurações).  
- **Admin técnico:** integração de WhatsApp, provisioning e billing/planos.

### Workflows críticos do negócio (Confirmado/Inferido)
1) **Onboarding**: criar workspace (tenant) + primeiro utilizador + login. (Confirmado em `/auth/signup`)
2) **Operação diária**: manter base de clientes + interações + agenda (appointments). (Confirmado em `/crm/*`)
3) **Recebimento de mensagens**: inbound WhatsApp → persistência e criação de interação. (Confirmado em `/messaging/inbound`)
4) **Visibilidade operacional**: dashboards/analytics de agenda e retenção básica. (Confirmado em `/analytics/*`)

### Estado de maturidade (síntese)
- **Produto / features core:** **MVP funcional** (Confirmado: customers, services, appointments, analytics, inbound WhatsApp).
- **Segurança e governança:** **insuficiente para scale enterprise** (Confirmado: ausência de RBAC; token custom; segredos versionados).
- **Operações (SRE/observability):** **não pronta** (Confirmado: observability stubs vazios; runbooks vazios).
- **Escala horizontal/assíncrono:** **risco elevado** (Confirmado: billing in-memory; dependência de Redis sem compose; contradição RLS/lookup webhook).

### Deployment blockers (P0) — “não escalar antes de corrigir”
1) **Segredos versionados** (possível acesso indevido ao DB/infra). (Confirmado em `.env`)
2) **Billing in-memory** (gates de feature tornam-se não determinísticos entre API e worker). (Confirmado no container e worker)
3) **RLS vs tenant resolution no inbound webhook** (webhooks podem falhar em Postgres com RLS). (Confirmado por desenho de policy e fluxo)

## 2) “As-is vs Target state” (visão executiva)

| Área | As-is (hoje) | Target state (recomendado) | Porquê (impacto) |
|---|---|---|---|
| Segredos | `.env` no repo com DB URL | Secrets fora do VCS + rotação + gestão | Reduz risco de incidente e compliance |
| Billing/entitlements | Subscription em memória | Subscription/entitlements persistidos (SQL) | Consistência API/worker e escala horizontal |
| Tenancy/RLS + webhook | Lookup de `whatsapp_accounts` antes de tenant context | Routing seguro sem depender de tenant context | Evita perda de mensagens / indisponibilidade |
| Autorização | Autenticação sem RBAC | RBAC mínimo (roles/memberships) | Previne abuso e suporta enterprise governance |
| Observability | Stubs vazios | Logs+metrics+tracing + runbooks | Operar com SLOs e incident response |
| CI/Test tooling | Sem CI, sem workflow documentado | CI (lint+tests) + docs de setup | Aumenta confiabilidade e velocidade |

## 3) Roadmap recomendado (0–30 / 30–60 / 60–90 dias)

> Datas e owners são **TBD** e devem ser acordados com liderança.

### 0–30 dias (P0/P1: estabilização e segurança)
- Remover `.env` do repo + **rotação** de credenciais (Security/Platform).
- Introduzir billing persistente (schema + repo SQL + wiring API/worker) (Backend).
- Resolver contradição RLS/lookup para inbound webhook (Backend/DB).
- Criar baseline de observability: request_id, logs estruturados e métricas mínimas (Platform).
- Adicionar Redis e worker no compose + runbook local-dev (DevEx).

### 30–60 dias (governança + robustez)
- RBAC mínimo e autorização por rotas sensíveis (Billing/Tenants/Admin).
- Token hardening (JWT + `kid` + rotação; refresh/revogação conforme necessidade).
- Padronizar tenancy header e contracts (backend + frontend).
- CI mínimo: lint/format, unit + API tests e gate em PR.

### 60–90 dias (escala e produto)
- Otimizar analytics (agregações no SQL / pre-aggregation assíncrona).
- Expandir observability (tracing end-to-end API → Celery; DLQ dashboards/alerts).
- Revisão de modelo de dados para crescimento (índices, constraints, migrations hygiene).

## 4) Risk register (operacional)

Legenda:
- **Severidade:** impacto máximo se ocorrer (Crítico/Alto/Médio/Baixo)
- **Probabilidade:** chance no contexto esperado (Alta/Média/Baixa)
- **Confiança:** Confirmado / Inferido / Precisa validação

| Risk ID | Descrição | Severidade | Probabilidade | Business impact | Mitigação | Owner | Target date | Confiança |
|---|---|---|---|---|---|---|---|---|
| R-001 | Segredos/credenciais versionados no repo | Crítico | Alta | acesso indevido ao DB, incidente e custos | remover do VCS + rotação + secrets mgmt | TBD | TBD | Confirmado |
| R-002 | Billing in-memory (API/worker inconsistente) | Crítico | Alta | feature gates falham; WhatsApp pode “quebrar” | persistir subscriptions/entitlements | TBD | TBD | Confirmado |
| R-003 | RLS impede lookup de `whatsapp_accounts` no inbound | Crítico | Média/Alta | perda/atraso de mensagens; SLA afetado | roteamento seguro sem tenant context | TBD | TBD | Confirmado |
| R-004 | Falta de RBAC/autorização | Alto | Alta | abuso interno/conta comprometida; governança fraca | RBAC mínimo + permissões por rota | TBD | TBD | Confirmado |
| R-005 | Observability inexistente | Alto | Alta | operação cega; MTTR alto | logs+metrics+tracing + runbooks | TBD | TBD | Confirmado |
| R-006 | Token custom sem rotação/revogação | Alto | Média | incident response difícil | JWT + rotação + refresh/revogação | TBD | TBD | Confirmado |
| R-007 | Infra local incompleta (Redis/worker) | Alto | Alta | QA/dev lentos; bugs não reprodutíveis | compose + runbooks | TBD | TBD | Confirmado |
| R-008 | Header de tenant inconsistente | Médio | Média | bugs de integração e suporte | padronizar header/contract | TBD | TBD | Confirmado |
| R-009 | Analytics escala mal (agregação em memória) | Médio | Média | latência e custo | mover agregação para SQL/async | TBD | TBD | Confirmado |
| R-010 | Higiene repo (venv, __pycache__ committed) | Baixo/Médio | Alta | ruído, PRs ruidosos | .gitignore + limpeza | TBD | TBD | Confirmado |

## 5) Referências (para engenharia)

- Auditoria detalhada: `docs/audit/2026-04-09-technical-audit.md`
- Arquitetura e fluxos: `docs/audit/2026-04-09-system-purpose-architecture.md`
- Catálogo funcional: `docs/audit/2026-04-09-functional-catalog.md`
- Rastreabilidade: `docs/audit/2026-04-09-traceability-matrix.md`
- Modelo de domínio: `docs/audit/2026-04-09-domain-model-entity-map.md`
- Diagramas: `docs/audit/2026-04-09-data-flow-diagrams.md`

