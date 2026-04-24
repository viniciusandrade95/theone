# Assistant Conversation Analytics (MVP)

Objetivo: permitir auditoria real de conversas (dashboard + WhatsApp) por tenant, com reconstrução de turns, eventos principais e outcome, sem reescrever o sistema todo.

## O que foi reaproveitado

Persistência já existente:

- Dashboard assistant (proxy para `chatbot1`)
  - `chatbot_conversation_sessions` (`ChatbotConversationSessionORM`)
  - `chatbot_conversation_messages` (`ChatbotConversationMessageORM`)
- WhatsApp
  - `conversations` + `messages` (inbound)
  - `outbound_messages` (assistant replies e confirmações via templates)
- Assistant/operacional
  - `assistant_funnel_events` (event log/telemetria)
  - `assistant_prebook_requests` (idempotency + vínculo com `appointments`)
  - `assistant_handoffs`

## O que foi padronizado/adicionado

### Event log unificado (funnel)

`assistant_funnel_events` passa a ser o “join point” principal para analytics cross-surface, com novos eventos (taxonomia v1):

- `assistant_conversation_started`
- `assistant_conversation_reset`
- `assistant_prebook_failed`
- `assistant_customer_identity_missing`
- `assistant_customer_phone_missing`
- `assistant_operational_failed`

E emissão desses eventos em:

- `/api/chatbot/message` e `/api/chatbot/reset` (surface dashboard)
- WhatsApp inbound + bot reply (`InboundWebhookService`)
- `/crm/assistant/prebook` (inclui falhas/blocked reasons)
- conversão confirmada via operador ao atualizar appointment `pending -> booked` (agora tenta propagar `conversation_id`/`assistant_session_id` a partir do `assistant_prebook_requests`)

### Outcome (classificação final)

Outcome é derivado de sinais/eventos (não inventa detalhes):

- `completed_booking`: existe `assistant_conversion_confirmed`
- `completed_prebook`: existe `assistant_prebook_created`
- `handoff`: existe `assistant_handoff_created`
- `blocked_missing_data`: existe `assistant_customer_identity_missing` ou `assistant_customer_phone_missing`
- `failed_operational`: existe `assistant_prebook_failed` ou `assistant_operational_failed`
- `fallback_only`: existe `assistant_fallback` e nenhum outcome acima
- `unknown`: default

`abandoned_candidate` é apenas um heuristic flag (por default: `last_activity_at` > 24h), para triagem, nao como verdade absoluta.

## Endpoints (tenant-scoped)

Nota: endpoints retornando texto de conversa sao dados sensiveis (PII). Sao protegidos por auth (`require_user`) e tenant header.

### Listagem (sem texto)

`GET /analytics/assistant/conversations?from=<iso>&to=<iso>&page=1&page_size=50`

Opcional:
- `surface=dashboard|whatsapp`
- `outcome=<taxonomy>`

### Detalhe (com texto/turns)

`GET /analytics/assistant/conversations/{conversation_id}`

Retorna:
- metadata principal (tenant/surface/customer/session)
- `turns`: sequencia de mensagens (dashboard ou WhatsApp)
- `events`: eventos normalizados
- `outcome` + `signals`

### Resumo por outcome

`GET /analytics/assistant/outcomes?from=<iso>&to=<iso>`

## Limitacoes atuais

- WhatsApp inbound messages nao guardam `trace_id` como coluna; correlacao fina depende de eventos + outbound trace.
- `assistant_prebook` recebe `conversation_id` como opcional; se o caller (chatbot1) nao enviar, parte do vínculo ainda sera via `session_id`.
- Abandono ainda nao e um evento persistido (sem job de fechamento); apenas `abandoned_candidate`.

