# Contrato Técnico de Integração — `theone` + `chatbot1`

## Objetivo do documento
Este documento define o contrato técnico inicial entre o CRM `theone` e o motor conversacional `chatbot1`.

Este contrato existe para reduzir ambiguidade durante a implementação e alinhar:
- fronteira entre sistemas
- payloads
- responsabilidades
- sessão
- auth entre serviços
- tracing
- execução operacional

---

## Princípios do contrato

### 1. Source of truth
**O `theone` é a source of truth de negócio e operação.**

### 2. Papel do `chatbot1`
O `chatbot1` é um motor de:
- interpretação
- decisão FAQ vs workflow
- recolha de slots
- continuidade conversacional
- escrita/orquestração da resposta

### 3. Papel do `theone`
O `theone` é o sistema de:
- autenticação
- tenants
- customers
- services
- booking
- appointments
- handoff
- canais e operação real

### 4. Regra principal de identidade
- `theone.tenant_id` = `chatbot1.client_id`

---

## Arquitetura contratual

### Fluxo principal
1. O utilizador interage com o `theone`
2. O `theone` chama o `chatbot1`
3. O `chatbot1` devolve decisão + resposta + intenção operacional
4. Quando necessário, o `chatbot1` chama APIs reais do `theone` através de um connector dedicado
5. O `theone` persiste o resultado operacional

### Regra de rede
- O browser **não** chama diretamente o `chatbot1`
- O `theone` expõe uma camada server-side própria para a conversa
- O `chatbot1` comunica com o `theone` através de APIs autenticadas machine-to-machine

---

## Contrato 1 — `theone` -> `chatbot1`

### Endpoint inicial esperado no `chatbot1`
- Implementação local atual: `POST /message`
- Implementação local atual: `POST /reset`
- Nome histórico em docs antigas: `POST /chat`
- Nome histórico em docs antigas: `POST /chat/reset`
- `GET /health`

### Payload inicial mínimo para `/message`
```json
{
  "client_id": "tenant_123",
  "session_id": "session_abc",
  "message": "Quero marcar uma limpeza de pele amanhã às 15h"
}
```

### Payload recomendado para evolução de `/message`
```json
{
  "client_id": "tenant_123",
  "session_id": "session_abc",
  "message": "Quero marcar uma limpeza de pele amanhã às 15h",
  "surface": "dashboard",
  "actor_type": "staff",
  "actor_id": "user_456",
  "locale": "pt-PT",
  "context": {
    "conversation_id": "conv_789",
    "customer_id": "cust_001",
    "location_id": "loc_001",
    "booking_slug": null,
    "appointment_id": null
  }
}
```

### Campos obrigatórios na fase 1
- `client_id`
- `session_id`
- `message`

### Campos recomendados para fase 2
- `surface`
- `actor_type`
- `actor_id`
- `context`

---

## Contrato 2 — `chatbot1` -> `theone`

### Resposta atual esperada de `/message`
O `chatbot1` já devolve uma estrutura rica com:
- `trace_id`
- `client_id`
- `session_id`
- `route`
- `workflow`
- `answer`
- `no_evidence`
- `router`
- `workflow_plan`
- `writer`
- `workflow_result`
- `rag`
- `facts_hit`
- `operational`

### Resposta mínima usada pelo `theone` na fase 1
```json
{
  "trace_id": "trace_xyz",
  "client_id": "tenant_123",
  "session_id": "session_abc",
  "route": "workflow",
  "workflow": "book_appointment",
  "answer": "Perfeito. Que horário prefere?",
  "no_evidence": false
}
```

### Resposta recomendada a ser normalizada pelo `theone`
```json
{
  "trace_id": "trace_xyz",
  "conversation_id": "conv_789",
  "route": "workflow",
  "workflow": "book_appointment",
  "answer": "Perfeito. Que horário prefere?",
  "no_evidence": false,
  "workflow_plan": {...},
  "workflow_result": {...},
  "router": {...},
  "operational": {...}
}
```

### Regra de consumo no `theone`
O frontend do `theone` **não deve** depender diretamente do payload cru do `chatbot1`.
A camada `/api/chatbot/*` do `theone` deve normalizar a resposta para um formato estável do produto.

---

## Contrato 3 — Rotas internas do `theone`

### Rotas a criar no `theone`
#### 1. Enviar mensagem
- `POST /api/chatbot/message`

#### 2. Resetar conversa
- `POST /api/chatbot/reset`

#### 3. Listar conversas futuras
- `GET /api/chatbot/conversations`

#### 4. Obter conversa
- `GET /api/chatbot/conversations/:conversation_id`

### Payload recomendado para `POST /api/chatbot/message`
```json
{
  "conversation_id": "conv_789",
  "message": "Quero marcar amanhã às 15h"
}
```

### Resposta recomendada de `POST /api/chatbot/message`
```json
{
  "conversation_id": "conv_789",
  "session_id": "session_abc",
  "trace_id": "trace_xyz",
  "answer": "Perfeito. Que serviço deseja marcar?",
  "route": "workflow",
  "workflow": "book_appointment",
  "status": "ok"
}
```

### Regras da rota interna
A rota do `theone` deve:
- validar auth do utilizador
- resolver `tenant_id`
- criar ou obter `conversation_id`
- criar ou obter `chatbot_session_id`
- enviar payload ao `chatbot1`
- persistir request/response
- devolver resposta estável ao frontend

---

## Sessão e conversa

### Conceitos
#### `conversation_id`
Identidade da conversa no `theone`

#### `session_id`
Identidade da sessão no `chatbot1`

### Regra
- uma `conversation_id` do `theone` mapeia para uma `session_id` do `chatbot1`
- a `conversation_id` é a identidade de produto
- a `session_id` é a identidade de runtime conversacional

### Estrutura mínima recomendada no `theone`
```json
{
  "conversation_id": "conv_789",
  "tenant_id": "tenant_123",
  "user_id": "user_456",
  "customer_id": "cust_001",
  "chatbot_session_id": "session_abc",
  "surface": "dashboard",
  "status": "active",
  "created_at": "...",
  "updated_at": "..."
}
```

### Estados sugeridos de conversa
- `active`
- `closed`
- `handoff_pending`
- `handoff_completed`
- `error`

---

## Tracing e observabilidade

### Princípio
Toda interação deve ser rastreável ponta a ponta.

### Campo obrigatório
- `X-Trace-Id`

### Regra
- o `theone` gera `trace_id`
- envia para o `chatbot1`
- o `chatbot1` propaga esse `trace_id`
- qualquer chamada operacional do `chatbot1` para o `theone` deve incluir o mesmo `trace_id`

### Benefício
Isto permite seguir:
- input do utilizador
- decisão do motor
- ação operacional
- resultado final

---

## Auth entre serviços

### Regra de segurança
A comunicação entre `theone` e `chatbot1` deve ser machine-to-machine.

### Recomendação fase 1
- header com secret partilhado, por exemplo `X-Internal-Service-Key`
- allowlist de origem se aplicável
- timeout curto
- retries limitados

### Recomendação fase 2
- service token rotativo
- eventual assinatura de requests internas

### Regra importante
O `chatbot1` não deve confiar em dados sensíveis vindos do browser.
O `tenant_id` e o contexto devem ser resolvidos pelo `theone`.

---

## Contrato operacional — `chatbot1` chama o `theone`

### Objetivo
Substituir o `FakeCalendarConnector` por um conector real: `TheOneConnector`.

### Casos de uso que o connector deve suportar
1. `create_prebooking`
2. `create_consult_request`
3. `create_quote_request`
4. `cancel_request`
5. `reschedule_request`
6. `handoff_to_human`
7. `check_availability`

---

## Endpoints operacionais recomendados no `theone`

### Fase 1
#### 1. Prebooking / booking assistido
- `POST /crm/assistant/prebook`

#### 2. Consultation request
- `POST /crm/assistant/consult-request`

#### 3. Quote request
- `POST /crm/assistant/quote-request`

#### 4. Handoff
- `POST /crm/assistant/handoff`

### Fase 2
#### 5. Availability
- `GET /crm/assistant/availability`

#### 6. Cancel
- `POST /crm/assistant/cancel`

#### 7. Reschedule
- `POST /crm/assistant/reschedule`

---

## Payloads operacionais recomendados

### 1. `POST /crm/assistant/prebook`
```json
{
  "tenant_id": "tenant_123",
  "conversation_id": "conv_789",
  "session_id": "session_abc",
  "trace_id": "trace_xyz",
  "customer": {
    "customer_id": "cust_001",
    "name": "Maria",
    "phone": "+3519...",
    "email": "maria@email.com"
  },
  "booking": {
    "service_id": "svc_001",
    "location_id": "loc_001",
    "starts_at": "2026-04-15T15:00:00Z",
    "ends_at": "2026-04-15T16:00:00Z",
    "notes": "pedido via assistente"
  },
  "meta": {
    "surface": "dashboard",
    "actor_type": "staff",
    "actor_id": "user_456"
  }
}
```

### 2. `POST /crm/assistant/handoff`
```json
{
  "tenant_id": "tenant_123",
  "conversation_id": "conv_789",
  "session_id": "session_abc",
  "trace_id": "trace_xyz",
  "reason": "cliente pediu atendimento humano",
  "context": {
    "customer_id": "cust_001",
    "workflow": "book_appointment"
  }
}
```

### 3. `GET /crm/assistant/availability`
Query recomendada:
- `tenant_id`
- `service_id`
- `location_id`
- `date`
- `timezone`

---

## Respostas operacionais recomendadas

### Success
```json
{
  "ok": true,
  "reference": "PB000123",
  "status": "created",
  "message": "Pré-agendamento criado com sucesso.",
  "data": {...}
}
```

### Validation error
```json
{
  "ok": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Service is required.",
  "details": {...}
}
```

### Conflict
```json
{
  "ok": false,
  "error_code": "APPOINTMENT_OVERLAP",
  "message": "There is a conflict with another appointment.",
  "details": {
    "conflicts": [...] 
  }
}
```

---

## Idempotência

### Regra
Toda ação operacional disparada pelo `chatbot1` deve ter `idempotency_key`.

### Payload recomendado
```json
{
  "idempotency_key": "tenant_123:conv_789:workflow_book_appointment:step_final_confirm"
}
```

### Objetivo
Evitar:
- bookings duplicados
- cancelamentos repetidos
- requests múltiplos após retry

---

## Mapeamento inicial de entidades

### `theone` -> `chatbot1`

#### Tenant settings -> `ClientProfile`
- `business_name` -> `name`
- `default_timezone` -> facts.hours.timezone
- branding -> `extra`

#### Booking settings -> business rules
- `booking_enabled`
- `booking_slug`
- `public_business_name`
- `public_contact_phone`
- `public_contact_email`
- `min_booking_notice_minutes`
- `max_booking_notice_days`
- `auto_confirm_bookings`

#### Services -> `services`
- `service_id`
- `name`
- `duration_min`
- `price`
- `booking_mode`
- `price_mode`
- `requires_human_confirmation`
- `professionals`

#### Locations -> `facts.location` + `facts.hours`
- morada
- timezone
- horário
- telefone
- email

#### Policies -> `facts.policies`
- cancelamento
- remarcação
- atraso
- confirmação

#### Professionals -> `professionals`
- nome
- aliases
- specialties
- services

---

## Estratégia de grounding

### Curto prazo
Sync controlado do `theone` para o `chatbot1`.

### Médio prazo
Criar `TheOneClientProvider` ou equivalente para o `chatbot1` consultar dados vivos do `theone`.

### Regra de decisão
- fase 1: velocidade com controlo
- fase 2: menor drift e maior robustez

---

## Ordem recomendada de implementação

### Sprint / Bloco 1
1. Deploy do `chatbot1`
2. Rotas `/api/chatbot/message` e `/api/chatbot/reset` no `theone`
3. UI do assistente
4. Persistência de conversa/sessão
5. Tracing básico

### Sprint / Bloco 2
6. Definir endpoints operacionais do `theone`
7. Criar `TheOneConnector`
8. Ligar prebooking real
9. Ligar handoff real

### Sprint / Bloco 3
10. Ligar quote/consult request
11. Definir estratégia de grounding
12. Iniciar painel de AI settings / policies / FAQ

---

## Critérios de aceite iniciais

### Fase 1
- utilizador autenticado fala com o assistente no dashboard
- `tenant_id` é sempre propagado corretamente
- conversa persiste
- `trace_id` existe ponta a ponta
- o sistema responde sem expor o `chatbot1` diretamente ao browser

### Fase 2
- workflow confirmado gera efeito real no `theone`
- erros operacionais regressam com mensagem clara
- nenhuma ação é executada em duplicado por retry

---

## Open questions técnicas
1. Quais endpoints backend do `theone` já existem realmente para support de assistant operations?
2. Há já modelo interno para handoff?
3. Onde vivem professionals e policies no backend do `theone`?
4. O primeiro workflow real será prebooking ou booking confirmado?
5. Vamos começar com sync ou provider remoto para grounding?

---

## Próximo documento recomendado
Depois deste contrato, o próximo documento ideal é:

**`docs/chatbot1-integration-implementation-plan.md`**

Esse documento deve conter:
- backlog de implementação
- owners
- sequência por sprint
- dependências
- riscos
- critérios de done por task
