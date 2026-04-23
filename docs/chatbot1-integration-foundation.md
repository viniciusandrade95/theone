# Fundação da Integração `theone` + `chatbot1`

## Objetivo do documento
Este documento serve como base inicial de trabalho para a integração entre o CRM `theone` e o motor conversacional `chatbot1`.

A ideia é consolidar:
- o que já existe
- o que já foi entendido
- o que falta fazer
- as alterações aos planos iniciais
- a estratégia recomendada para uma integração smooth but robusta

---

## Princípio central
**O `theone` é a source of truth.**

Isto significa que:
- o estado real do tenant vive no `theone`
- os clientes vivem no `theone`
- os serviços vivem no `theone`
- a agenda vive no `theone`
- as regras de booking vivem no `theone`
- a configuração pública do negócio vive no `theone`
- o `chatbot1` deve funcionar como motor de compreensão, recolha de contexto e orquestração conversacional

---

## Estado atual — o que já foi entendido

### 1. `theone`
O `theone` já demonstra maturidade como CRM operacional multi-tenant.

#### O que já identificámos
- Login com `token` e `tenant_id`
- Proteção de rotas de dashboard
- Dashboard operacional com overview, quick actions e métricas
- Gestão de customers
- Gestão de appointments
- Booking público por slug
- Settings gerais do tenant
- Settings de online booking
- Superfície admin para WhatsApp accounts

#### Campos já identificados como relevantes para a integração
##### Tenant settings
- `business_name`
- `default_timezone`
- `currency`
- `primary_color`
- `logo_url`

##### Booking settings
- `booking_enabled`
- `booking_slug`
- `public_business_name`
- `public_contact_phone`
- `public_contact_email`
- `min_booking_notice_minutes`
- `max_booking_notice_days`
- `auto_confirm_bookings`

##### Appointments
- `customer_id`
- `location_id`
- `service_id`
- `starts_at`
- `ends_at`
- `status`
- `cancelled_reason`
- `notes`

##### Customers
- `name`
- `phone`
- `email`
- `stage`

#### Conclusão sobre o `theone`
O `theone` já está numa posição muito boa para ser a fonte real de dados operacionais e contextuais da integração.

---

### 2. `chatbot1`
O `chatbot1` já demonstra maturidade como motor conversacional multi-tenant.

#### O que já identificámos
- Runtime FastAPI local com `/message`, `/reset` e `/health`
- Referências antigas a `/chat` e `/chat/reset` devem ser lidas como nomes históricos do contrato inicial.
- Input principal com `client_id`, `session_id` e `message`
- Output rico com `route`, `workflow`, `answer`, `router`, `workflow_result`, `rag`, `facts_hit`, `operational`
- Multi-tenancy via `ClientRegistry`
- Profile, facts, understanding, services e KB por tenant
- Routing entre `smalltalk`, `rag` e `workflow`
- Workflow engine com estado por sessão
- Continuidade conversacional e gestão de slot filling

#### Estado operacional local atual
O `chatbot1` já tem `TheOneConnector` para a integração local com `theone`,
incluindo prebooking via `/crm/assistant/prebook`. O `FakeCalendarConnector`
continua útil como fallback/test double, mas já não deve ser descrito como o
centro do fluxo local validado.

#### Conclusão sobre o `chatbot1`
O `chatbot1` deve ser preservado como motor conversacional. No estado local
atual, o fluxo validado já usa `TheOneConnector` para prebooking com o `theone`;
o `FakeCalendarConnector` permanece como fallback/test double, não como centro
da integração local.

---

## Mapeamento estratégico inicial

### Regra principal de identidade
- `theone.tenant_id` = `chatbot1.client_id`

### Regra principal de arquitetura
- Browser fala com `theone`
- `theone` fala com `chatbot1`
- `chatbot1` fala com APIs reais do `theone` para ações operacionais

### Regra principal de responsabilidade
#### `theone`
- source of truth
- gestão de auth e permissões
- gestão de tenant
- gestão de customers
- gestão de appointments
- gestão de booking
- gestão de canais
- persistência da conversa no produto

#### `chatbot1`
- compreensão da intenção
- decisão entre FAQ vs workflow
- recolha de slots
- gestão do estado da conversa
- escrita da resposta
- orquestração do fluxo

---

## O que já foi decidido até aqui

### 1. A integração não deve ser direta do browser para o `chatbot1`
Decisão mantida.

**Motivo:**
- segurança
- controlo de sessão
- controlo de tenant
- observabilidade
- desacoplamento

### 2. O `chatbot1` não deve ser embutido dentro do `theone`
Decisão mantida.

**Motivo:**
- separação clara de responsabilidades
- deploy independente
- manutenção mais simples
- possibilidade de escalar o motor conversacional separadamente

### 3. O primeiro caso de uso deve acontecer dentro do dashboard do `theone`
Decisão mantida.

**Motivo:**
- risco menor
- melhor controlo
- facilita QA
- evita abrir de início canais mais sensíveis

---

## O que já foi feito na análise

### Trabalho já realizado
- análise estrutural do repositório `theone`
- análise estrutural do repositório `chatbot1`
- identificação das principais peças de domínio dos dois lados
- identificação dos maiores gaps de integração
- definição da arquitetura recomendada de alto nível
- definição do princípio de source of truth no `theone`
- validação local do proxy `theone` -> `chatbot1`
- validação local do `TheOneConnector` para prebooking
- fechamento da fase de testes do chatbot com sidequest/hybrid/autonomous verdes

### Principais conclusões já obtidas
1. O `theone` está suficientemente maduro para ser a fonte operacional.
2. O `chatbot1` está suficientemente maduro para ser o motor de conversa.
3. A ligação é viável e forte.
4. O ponto crítico deixou de ser a ligação básica entre conversa e execução real; o próximo foco é grounding por tenant e piloto controlado.

---

## O que falta fazer

### Bloco A — grounding do tenant piloto
Ainda falta consolidar, para o tenant piloto:
- `profile.yaml`
- `kb/services.json`
- `kb/facts.yaml`
- FAQ/policies reais
- aliases de serviços
- timezone e regras operacionais

### Bloco B — piloto controlado
Ainda falta definir:
- tenant piloto
- checklist de demo/piloto
- perguntas e fluxos mínimos esperados
- critérios de blocker vs melhoria

### Bloco C — hardening pós-verde
Ainda falta continuar, sem reabrir a fase fechada:
- robustez conversacional curta
- correção de slots sem perda de contexto
- FAQ genérica mais consistente
- fechamento pós-sucesso

### Bloco D — documentação operacional
O runbook consolidado atual é:

```text
/home/vinicius/system-audit/workspace/LOCAL_RUNBOOK.md
```

### Bloco E — grounding por tenant
Ainda falta consolidar:
- como o `chatbot1` recebe profile, facts, services, professionals e policies do `theone`
- se vamos usar sync inicial ou provider remoto
- como o tenant vai gerir FAQ/policies/dados usados no RAG

### Bloco F — observabilidade e rollout
Ainda falta consolidar:
- logs ponta a ponta
- tracing consistente
- métricas de conversa
- plano de rollout interno
- tenants piloto

---

## Alterações aos planos iniciais

### Plano inicial anterior
A ideia inicial poderia sugerir uma ligação mais rápida através de um simples consumo de `/chat`.

### Alteração de plano
Esse plano foi ajustado.

#### Novo entendimento
Não basta ligar o `theone` a um endpoint conversacional bruto.
É necessário tratar a integração como uma ligação entre:
- sistema operacional de negócio (`theone`)
- motor conversacional (`chatbot1`)

#### Consequência prática
O plano passa a exigir:
- uma camada de proxy/control plane no `theone`
- uma camada operacional real no `chatbot1`
- uma forma robusta de grounding por tenant

---

## Estratégia recomendada por etapas

# Etapa 0 — Foundation
## Objetivo
Fechar arquitetura, contratos e responsabilidades.

## O que fazer
- confirmar o `theone` como source of truth
- fechar mapeamento `tenant_id -> client_id`
- inventariar APIs reais do backend do `theone`
- definir contrato de integração inicial
- definir o primeiro caso de uso da release

## Estado
Em progresso conceitual. Ainda falta transformar isto em contrato técnico detalhado.

## Alteração face ao plano inicial
Antes: começar logo pela integração funcional.
Agora: fechar primeiro a arquitetura e o contrato.

---

# Etapa 1 — Integração mínima segura
## Objetivo
Ter o `chatbot1` acessível no `theone` sem ainda depender de automação real completa.

## O que fazer
- subir o `chatbot1` como serviço isolado
- criar rotas server-side no `theone`
- criar UI do assistente no dashboard
- persistir `conversation_id` / `session_id`
- permitir FAQ, smalltalk e handoff básico

## Estado
Ainda não implementado.

## Alteração face ao plano inicial
Mantida, mas reforçada com a exigência de persistência de conversa e proxy interno.

---

# Etapa 2 — Ligação operacional real
## Objetivo
Substituir execução fake por ações reais no `theone`.

## O que fazer
- criar `TheOneConnector`
- ligar prebooking/booking assistido ao CRM real
- ligar quote request
- ligar consultation request
- ligar handoff
- decidir com cautela cancelamento e remarcação

## Estado
Ainda não implementado.

## Alteração face ao plano inicial
Antes: podia parecer aceitável manter parte fake por mais tempo.
Agora: o plano foi endurecido; a troca do fake connector é considerada central para a integração verdadeira.

---

# Etapa 3 — Grounding real por tenant
## Objetivo
Fazer o `chatbot1` responder com contexto real e atualizado do `theone`.

## O que fazer
- mapear `theone` -> `ClientProfile`
- mapear `theone` -> services
- mapear `theone` -> facts / policies / professionals
- decidir entre sync de ficheiros ou provider remoto
- montar base inicial de FAQ/policies

## Estado
Ainda não implementado.

## Alteração face ao plano inicial
Antes: KB por ficheiro local parecia suficiente.
Agora: isso é visto como solução de curto prazo; o plano de médio prazo é provider remoto ou sincronização mais robusta.

---

# Etapa 4 — Observabilidade, segurança e rollout
## Objetivo
Lançar de forma controlada.

## O que fazer
- propagar `trace_id`
- adicionar logs de conversa
- definir métricas mínimas
- controlar rollout por tenant piloto
- endurecer auth e permissões antes de expandir superfícies

## Estado
Ainda não implementado.

## Alteração face ao plano inicial
Antes: podia entrar mais tarde.
Agora: passa a ser considerado necessário antes de escalar para canais externos.

---

## Estratégia de execução recomendada para a equipa

### Senior Software Engineer
Owner de:
- arquitetura
- contratos de integração
- `TheOneConnector`
- observabilidade
- persistência de sessão
- segurança entre serviços

### Fullstack Developer
Owner de:
- UI do assistente
- rotas proxy do `theone`
- camada frontend/server-side do `theone`
- estados de loading/error/retry
- painel inicial de gestão se necessário

### Apoio transversal
Owner de:
- casos de uso
- QA manual
- documentação funcional
- tenants piloto
- definição de FAQ/policies iniciais
- ajuda na criação de dados e testes

---

## Backlog inicial proposto

### Prioridade P0
- mapear endpoints reais do backend do `theone`
- criar documento de contrato de integração
- subir `chatbot1`
- criar `/api/chatbot/message`
- criar `/api/chatbot/reset`
- criar UI interna no dashboard
- persistir `conversation_id`

### Prioridade P1
- criar `TheOneConnector`
- ligar prebooking real
- ligar handoff real
- ligar quote/consultation request
- propagar `trace_id`

### Prioridade P2
- grounding por tenant
- sync/settings/policies/professionals
- métricas e rollout controlado
- plano de expansão para booking público e WhatsApp

---

## Open questions
Estas perguntas ainda precisam de resposta objetiva antes de avançar demasiado:

1. Quais endpoints do backend do `theone` já existem de forma real, para além do que o frontend mostra?
2. Existe já backend para leads, quote request, consultation request e handoff?
3. Como o `theone` representa professionals e policies no backend?
4. Qual é a forma preferida para o grounding inicial?
   - sync por ficheiro
   - provider remoto
   - híbrido
5. O primeiro workflow real deve ser:
   - prebooking
   - booking confirmado
   - quote request
   - handoff

---

## Recomendação final atual
A melhor estratégia continua a ser:
1. usar o `theone` como source of truth
2. usar o `chatbot1` como motor conversacional
3. começar pelo dashboard interno
4. trocar a execução fake por execução real o mais cedo possível
5. só depois expandir para booking público e canais externos

---

## Próximo documento recomendado
Depois deste ficheiro inicial, o próximo documento que devemos produzir é:

**`docs/chatbot1-integration-contract.md`**

Esse documento deve conter:
- payloads
- endpoints
- eventos
- decisões de auth
- decisões de idempotência
- mapeamento técnico entre entidades do `theone` e estruturas do `chatbot1`
