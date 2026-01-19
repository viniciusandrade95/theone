# Repo Map — Beauty & Lifestyle SaaS CRM

Este documento explica a estrutura do repositório e onde cada tipo de código deve viver.
Objetivo: onboarding em menos de 10 minutos.

---

## Visão Geral

Este projeto segue um **monólito modular por domínio**.

- Um único repositório
- Módulos isolados por domínio de negócio
- Infra e cross-cutting separados em `core/`
- Trabalho pesado sempre fora do ciclo de request

---

## Estrutura Principal

### `/core`
Infraestrutura compartilhada e preocupações transversais.

**Não contém regras de negócio.**

- `config/` — carregamento e validação de env vars
- `security/` — autenticação, hashing, permissões
- `tenancy/` — resolução e enforcement de tenant
- `events/` — event bus interno
- `observability/` — logs, métricas, tracing
- `errors/` — erros tipados e mapeamento HTTP

---

### `/modules`
Onde o produto vive.  
Cada pasta representa **um domínio de negócio**.

Exemplos:
- `crm/` — clientes, histórico, pipeline
- `messaging/` — WhatsApp, mensagens, automações
- `billing/` — planos, subscrições, limites
- `analytics/` — KPIs e métricas do negócio

#### Estrutura padrão de um módulo
