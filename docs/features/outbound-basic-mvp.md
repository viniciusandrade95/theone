# Outbound Básico (MVP)

## Objetivo
Permitir comunicação outbound **simples e rastreável** (principalmente 1:1) com clientes, com:
- templates por tenant
- preview com variáveis simples
- envio manual assistido (WhatsApp deeplink) **ou** envio provider-backed quando configurado
- histórico no perfil do cliente
- criação automática de interaction quando o envio é iniciado com sucesso

> Este MVP **não** é automação de marketing, mas agora suporta **lifecycle de entrega** quando o provider está configurado.

## Scope implementado
### Templates
- CRUD em `/crm/outbound/templates`
- `type` suportados:
  - `booking_confirmation`, `reminder_24h`, `reminder_3h`, `post_service_followup`, `review_request`, `reactivation`, `simple_campaign`, `tomorrow_open_slot`, `internal_followup_support`
- Variáveis suportadas:
  - `{{customer_name}}`
  - `{{appointment_date}}`, `{{appointment_time}}`
  - `{{service_name}}`, `{{location_name}}`
  - `{{business_name}}`

### Preview e envio manual
- Preview: `POST /crm/outbound/preview` (renderiza e valida contexto)
- Envio: `POST /crm/outbound/send`
  - preferencialmente envia via provider (WhatsApp Cloud) se configurado + tenant tiver `whatsapp_accounts` ativo
  - fallback: gera deeplink `wa.me` (envio assistido)
  - guarda histórico em `outbound_messages` (inclui `provider_message_id` quando aplicável)
  - cria interaction `outbound_whatsapp` quando o envio é iniciado com sucesso
- Reenvio: `POST /crm/outbound/{id}/resend` (apenas para mensagens `failed`)

### Histórico
- Listagem: `GET /crm/outbound/messages` com filtros por `customer_id`, `template_id`, `type`, `status`
- UI: histórico aparece no customer profile no dashboard.

## Significado de status (importante)
Estados mínimos (compat): `pending`, `sent`, `failed` (e `delivered` quando callbacks chegam).

O campo `status` mantém compatibilidade com o histórico/UI atual. Para tracking real, usar `delivery_status`:

- `delivery_status=queued`: criado e aguardando envio provider-backed.
- `delivery_status=accepted`: provider aceitou o envio e devolveu `provider_message_id`.
- `delivery_status=delivered/read`: provider confirmou entrega/leitura via callback.
- `delivery_status=failed`: falhou (preparação ou provider).
- `delivery_status=unconfirmed`: fallback deeplink; não existe confirmação de entrega do provider.

## Interactions
Quando uma mensagem outbound fica com `status=sent`, é criada uma interaction no CRM:
- `type`: `outbound_whatsapp`
- `content`: corpo final renderizado/enviado

## Callbacks de entrega (provider-backed)

- Endpoint: `POST /messaging/delivery` (sem tenant header; tenant é resolvido por `phone_number_id`)
- Dedupe: por `(tenant_id, provider, external_event_id)` em `outbound_delivery_events`
- Atualiza `outbound_messages.delivery_status` e timestamps (`delivered_at`, `failed_at`)

Variáveis de ambiente relevantes:
- `WHATSAPP_WEBHOOK_SECRET` (verificação de assinatura do callback)
- `WHATSAPP_CLOUD_ACCESS_TOKEN`, `WHATSAPP_CLOUD_API_VERSION`, `WHATSAPP_CLOUD_TIMEOUT_SECONDS` (envio via provider)

## Fora de scope neste PR
- automações e gatilhos automáticos
- múltiplos canais
- campanhas massivas / segmentação / journeys
