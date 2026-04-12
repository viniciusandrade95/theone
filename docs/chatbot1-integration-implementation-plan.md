# Plano de Implementação — Integração `theone` + `chatbot1`

## Objetivo do documento
Este documento traduz a estratégia e o contrato da integração entre `theone` e `chatbot1` num plano de execução real.

O objetivo é dar à equipa um plano que responda a estas perguntas:
- o que fazer primeiro
- quem é responsável por cada bloco
- quais são as dependências
- quais os riscos
- quando uma task está realmente done

---

## Contexto consolidado

### Verdade principal
**O `theone` é a source of truth.**

### Papel do `chatbot1`
Motor de:
- compreensão
- decisão FAQ vs workflow
- slot filling
- continuidade da conversa
- escrita/orquestração da resposta

### Arquitetura recomendada
- browser fala com `theone`
- `theone` fala com `chatbot1`
- `chatbot1` chama APIs reais do `theone` para ações operacionais

---

## Objetivo da release inicial
Entregar uma integração interna, robusta e controlada, no dashboard do `theone`, que permita:
- conversar com o assistente
- responder FAQ do negócio
- iniciar workflows simples
- gerar ações reais ou semirreais no CRM através de uma camada controlada

### Fora de scope da primeira release
- WhatsApp completo
- booking conversacional público completo
- automações irreversíveis sem validação
- rollout multi-canal total

---

## Equipa e ownership

### 1. Senior Software Engineer
**Owner técnico da espinha dorsal da integração**

Responsabilidades:
- arquitetura da integração
- contratos entre sistemas
- `TheOneConnector`
- persistência de sessão/conversa
- segurança entre serviços
- tracing e observabilidade
- revisão de design e hardening

### 2. Fullstack Developer
**Owner da experiência e camada de produto no `theone`**

Responsabilidades:
- UI do assistente
- rotas `/api/chatbot/*`
- integração frontend/server-side
- estados de loading/error/retry
- persistência e consumo da conversa no `theone`
- eventuais settings operacionais do assistente

### 3. Apoio transversal / operação / produto
**Owner de execução transversal, definição funcional e QA**

Responsabilidades:
- definição de casos de uso
- documentação funcional
- validação de fluxos
- QA manual
- montagem de tenants piloto
- definição de FAQ/policies iniciais
- acompanhamento de rollout

---

## Fases de implementação

# Fase 0 — Foundation & Discovery
## Objetivo
Fechar a base técnica e funcional antes de codar a integração profunda.

## Deliverables
- inventário de endpoints reais do backend do `theone`
- definição de caso de uso da release 1
- confirmação do contrato base entre os dois sistemas
- mapeamento inicial de entidades

## Tasks
### T0.1 — Inventariar backend real do `theone`
**Owner:** Senior Software Engineer  
**Apoio:** Fullstack + produto

#### Descrição
Levantar quais endpoints existem de facto no backend do `theone` e não apenas no frontend.

#### Perguntas que esta task tem de responder
- existe endpoint real para `customers`?
- existe endpoint real para `appointments`?
- existe endpoint real para `services`?
- existe endpoint real para `booking settings`?
- existe endpoint real para `locations`?
- existe endpoint real para `handoff`?
- existe endpoint real para `quote request`?
- existe endpoint real para `consult request`?
- existe endpoint real para `availability`?

#### Output esperado
Uma tabela simples com:
- endpoint
- método
- existe
- pronto para uso
- precisa adaptação
- notes

#### Dependências
Nenhuma.

#### Definition of Done
- lista consolidada de endpoints reais
- dúvidas críticas assinaladas
- partilhado com a equipa

---

### T0.2 — Fechar scope da release 1
**Owner:** Produto / apoio transversal  
**Apoio:** Senior Engineer

#### Descrição
Escolher quais capacidades entram na primeira release interna.

#### Recomendação atual
Entram:
- dashboard assistant
- FAQ
- handoff
- prebooking / booking assistido controlado

Não entram:
- WhatsApp completo
- automação avançada de cancelamento/remarcação
- site público conversacional completo

#### Definition of Done
- scope fechado por escrito
- alinhamento de equipa
- lista de fora de scope explícita

---

### T0.3 — Fechar contrato técnico inicial
**Owner:** Senior Software Engineer

#### Descrição
Validar e congelar a v1 do contrato descrito em `docs/chatbot1-integration-contract.md`.

#### Definition of Done
- campos obrigatórios definidos
- naming alinhado
- headers de tracing definidos
- auth M2M definido para fase 1

---

# Fase 1 — Integração mínima segura
## Objetivo
Ligar `theone` e `chatbot1` no dashboard, sem expor o motor diretamente ao browser.

## Deliverables
- `chatbot1` deployado
- proxy interno no `theone`
- UI inicial do assistente
- conversa persistida no produto
- tracing básico ponta a ponta

## Tasks
### T1.1 — Deploy do `chatbot1`
**Owner:** Senior Software Engineer

#### Descrição
Subir o `chatbot1` como serviço separado em ambiente controlado.

#### Output esperado
- URL interna de serviço
- healthcheck funcional
- env vars configuradas
- logs visíveis

#### Dependências
T0.3

#### Definition of Done
- `/health` responde 200
- `/chat` responde com contrato válido
- `X-Trace-Id` suportado

---

### T1.2 — Criar rotas internas `/api/chatbot/*` no `theone`
**Owner:** Fullstack Developer  
**Apoio:** Senior Engineer

#### Descrição
Criar:
- `POST /api/chatbot/message`
- `POST /api/chatbot/reset`

Estas rotas devem:
- validar auth do utilizador
- resolver `tenant_id`
- gerir `conversation_id`
- chamar o `chatbot1`
- normalizar a resposta

#### Dependências
T1.1

#### Definition of Done
- frontend consegue usar as rotas
- browser não chama o `chatbot1` diretamente
- `tenant_id` é enviado como `client_id`

---

### T1.3 — Criar modelo de conversa no `theone`
**Owner:** Senior Software Engineer

#### Descrição
Criar persistência mínima de conversa/sessão.

#### Campos mínimos recomendados
- `conversation_id`
- `tenant_id`
- `user_id`
- `customer_id` opcional
- `chatbot_session_id`
- `surface`
- `status`
- timestamps

#### Dependências
T0.3

#### Definition of Done
- conversa pode ser criada e retomada
- `chatbot_session_id` fica persistido
- conversa sobrevive ao refresh da página

---

### T1.4 — Criar UI inicial do assistente no dashboard
**Owner:** Fullstack Developer

#### Descrição
Criar a primeira superfície de uso real.

#### Escopo UI mínimo
- histórico da conversa
- input de mensagem
- botão enviar
- botão nova conversa
- loading
- erro

#### Dependências
T1.2, T1.3

#### Definition of Done
- utilizador autenticado conversa com o assistente
- resposta é visível
- reset funciona
- UX estável em estados principais

---

### T1.5 — Tracing ponta a ponta inicial
**Owner:** Senior Software Engineer

#### Descrição
Propagar `trace_id` entre:
- frontend
- `theone`
- `chatbot1`

#### Dependências
T1.1, T1.2

#### Definition of Done
- cada request tem `trace_id`
- logs do `theone` e `chatbot1` conseguem ser correlacionados

---

# Fase 2 — Execução operacional real
## Objetivo
Trocar a execução fake do `chatbot1` por integração com o domínio real do `theone`.

## Deliverables
- `TheOneConnector`
- endpoints operacionais no `theone`
- prebooking/handoff reais
- idempotência mínima

## Tasks
### T2.1 — Definir endpoints operacionais do `theone`
**Owner:** Senior Software Engineer

#### Descrição
Definir e/ou implementar os endpoints que o `chatbot1` vai consumir.

#### Ordem recomendada
1. `POST /crm/assistant/prebook`
2. `POST /crm/assistant/handoff`
3. `POST /crm/assistant/quote-request`
4. `POST /crm/assistant/consult-request`
5. `GET /crm/assistant/availability`
6. `POST /crm/assistant/cancel`
7. `POST /crm/assistant/reschedule`

#### Dependências
T0.1

#### Definition of Done
- endpoints definidos
- payloads alinhados ao contrato
- respostas normalizadas

---

### T2.2 — Criar `TheOneConnector` no `chatbot1`
**Owner:** Senior Software Engineer

#### Descrição
Substituir a execução via `FakeCalendarConnector` por um connector real contra o `theone`.

#### Casos iniciais obrigatórios
- `create_prebooking`
- `handoff`

#### Casos seguintes
- `create_quote_request`
- `create_consult_request`
- `check_availability`
- `cancel_request`
- `reschedule_request`

#### Dependências
T2.1

#### Definition of Done
- o workflow engine já não depende do fake connector para os casos ativos da release
- erros do `theone` são tratados corretamente
- resposta final ao utilizador continua conversacional

---

### T2.3 — Implementar idempotência mínima
**Owner:** Senior Software Engineer

#### Descrição
Adicionar `idempotency_key` às ações operacionais disparadas pelo `chatbot1`.

#### Dependências
T2.1, T2.2

#### Definition of Done
- retries não geram duplicados
- a key estável é previsível por workflow e conversa

---

### T2.4 — Expor estado operacional no `theone`
**Owner:** Fullstack Developer

#### Descrição
Garantir que o resultado operacional é visível no produto.

Exemplos:
- prebooking criado
- handoff aberto
- pedido de consulta registado

#### Dependências
T2.2

#### Definition of Done
- utilizador consegue confirmar no `theone` que a ação realmente existiu

---

# Fase 3 — Grounding por tenant
## Objetivo
Fazer o `chatbot1` responder com informação certa, atualizada e específica do tenant.

## Deliverables
- estratégia inicial de grounding implementada
- mapping de settings/services/policies/professionals
- dados de FAQ/policies preparados

## Tasks
### T3.1 — Fechar estratégia de grounding
**Owner:** Senior Software Engineer  
**Apoio:** Produto

#### Opções
- sync controlado para ficheiros/artefactos consumidos pelo `chatbot1`
- provider remoto
- híbrido

#### Recomendação atual
- fase 1/2: sync controlado
- fase 3+: provider remoto

#### Definition of Done
- decisão tomada
- implicações técnicas documentadas

---

### T3.2 — Mapear `theone` -> profile/facts/services/professionals
**Owner:** Senior Software Engineer

#### Descrição
Transformar dados reais do `theone` em estruturas consumíveis pelo `chatbot1`.

#### Fontes principais
- settings gerais
- booking settings
- services
- locations
- professionals
- policies

#### Dependências
T0.1, T3.1

#### Definition of Done
- mapping implementado
- pelo menos 1 tenant piloto com grounding funcional

---

### T3.3 — Criar conteúdo inicial de FAQ/policies
**Owner:** Produto / apoio transversal  
**Apoio:** Fullstack se houver UI

#### Descrição
Preparar conteúdo inicial de negócio para grounding.

#### Conteúdo mínimo
- horário
- morada
- contacto
- serviços
- formas de pagamento
- política de cancelamento
- política de remarcação
- atraso
- confirmação

#### Dependências
T3.1

#### Definition of Done
- tenant piloto tem FAQ/policies preenchidos
- o assistente responde com grounding verificável

---

# Fase 4 — Hardening e rollout
## Objetivo
Lançar com controlo e preparar escalabilidade.

## Deliverables
- métricas mínimas
- rollout interno controlado
- tenants piloto
- plano de evolução

## Tasks
### T4.1 — Instrumentar métricas mínimas
**Owner:** Senior Software Engineer

#### Métricas recomendadas
- nº de conversas
- taxa de erro
- latência média
- `% faq`
- `% workflow`
- `% handoff`
- `% no_evidence`
- `% workflows concluídos`

#### Definition of Done
- métricas acessíveis à equipa
- baseline inicial disponível

---

### T4.2 — Pilotar com 1 tenant real
**Owner:** Produto / apoio transversal

#### Descrição
Escolher 1 tenant piloto com dados suficientes e testar o fluxo de ponta a ponta.

#### Definition of Done
- tenant piloto configurado
- fluxo testado em cenários reais
- issues recolhidas e priorizadas

---

### T4.3 — QA funcional estruturado
**Owner:** Produto / apoio transversal  
**Apoio:** Fullstack

#### Cenários mínimos
- FAQ simples
- pergunta sem evidência
- início de agendamento
- recolha de slots
- confirmação
- prebooking criado
- handoff
- erro operacional
- reset de conversa

#### Definition of Done
- checklist executada
- bugs classificados por severidade

---

## Sequência recomendada de implementação

### Ordem 1 — tornar possível
- T0.1
- T0.2
- T0.3
- T1.1
- T1.2
- T1.3
- T1.4
- T1.5

### Ordem 2 — tornar real
- T2.1
- T2.2
- T2.3
- T2.4

### Ordem 3 — tornar bom
- T3.1
- T3.2
- T3.3

### Ordem 4 — tornar lançável
- T4.1
- T4.2
- T4.3

---

## Dependências críticas

### Dependência 1
Sem inventário real do backend do `theone`, a integração operacional corre o risco de ser desenhada em cima de suposições.

### Dependência 2
Sem proxy server-side no `theone`, o desenho fica frágil e inseguro.

### Dependência 3
Sem substituir o `FakeCalendarConnector`, não existe integração operacional verdadeira.

### Dependência 4
Sem grounding mínimo por tenant, o assistente pode parecer “genérico” e perder valor.

---

## Principais riscos

### R1 — Drift entre `theone` e `chatbot1`
**Mitigação:** sync controlado no curto prazo e provider remoto no médio prazo.

### R2 — Execução operacional duplicada
**Mitigação:** idempotência obrigatória.

### R3 — Sessão perder-se entre deploys/instâncias
**Mitigação:** persistência da conversa no `theone` e, idealmente, evolução da sessão do `chatbot1` para store partilhada.

### R4 — Superfície de segurança fraca
**Mitigação:** browser não fala com `chatbot1`; auth M2M; revisão posterior de auth do `theone`.

### R5 — Scope creep
**Mitigação:** dashboard first, sem WhatsApp first.

---

## Definition of Done da release inicial
A release inicial está done quando:

1. Um utilizador autenticado consegue falar com o assistente no dashboard do `theone`
2. O `tenant_id` é corretamente usado como `client_id`
3. A conversa persiste no produto
4. O `chatbot1` responde através do `theone`, não diretamente no browser
5. Existe `trace_id` ponta a ponta
6. Pelo menos um workflow operacional real funciona
7. O resultado operacional é verificável dentro do `theone`
8. Existe pelo menos 1 tenant piloto funcional

---

## Checklist executiva resumida

### Já alinhado
- `theone` é source of truth
- `chatbot1` é motor conversacional
- dashboard é a superfície inicial
- browser não fala direto com o `chatbot1`

### Fazer agora
- inventário do backend do `theone`
- fechar contrato v1
- deploy do `chatbot1`
- proxy `/api/chatbot/*`
- UI inicial
- persistência de conversa

### Fazer em seguida
- `TheOneConnector`
- prebooking real
- handoff real
- idempotência
- grounding do tenant piloto

---

## Próximo artefacto recomendado
O próximo artefacto ideal, depois deste documento, é um board operacional simples com:
- task
- owner
- estado
- bloqueios
- data alvo

Sugestão de nome:

**`docs/chatbot1-integration-tracker.md`**
