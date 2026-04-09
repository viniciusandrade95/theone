# Outbound Básico (MVP)

## Objetivo
Permitir comunicação outbound **simples e rastreável** (principalmente 1:1) com clientes, com:
- templates por tenant
- preview com variáveis simples
- envio manual assistido (WhatsApp deeplink)
- histórico no perfil do cliente
- criação automática de interaction quando o envio é iniciado com sucesso

> Este MVP **não** é automação de marketing nem confirma entrega no provider.

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
  - gera deeplink `wa.me`
  - guarda histórico em `outbound_messages`
  - cria interaction `outbound_whatsapp` quando o envio é iniciado com sucesso
- Reenvio: `POST /crm/outbound/{id}/resend` (apenas para mensagens `failed`)

### Histórico
- Listagem: `GET /crm/outbound/messages` com filtros por `customer_id`, `template_id`, `type`, `status`
- UI: histórico aparece no customer profile no dashboard.

## Significado de status (importante)
Estados mínimos: `pending`, `sent`, `failed`.

- `pending`: mensagem criada mas ainda não enviada (reservado para futuras automações/filas).
- `sent`: **no MVP significa envio assistido iniciado pelo utilizador** (deeplink gerado e ação disparada).  
  **Não** significa entrega confirmada por provider.
- `failed`: falhou preparar/enviar pelo pathway (ex.: customer sem telefone válido).

## Interactions
Quando uma mensagem outbound fica com `status=sent`, é criada uma interaction no CRM:
- `type`: `outbound_whatsapp`
- `content`: corpo final renderizado/enviado

## Fora de scope neste PR
- automações e gatilhos automáticos
- integração real com provider (delivery receipts, retries, rate limiting)
- múltiplos canais
- campanhas massivas / segmentação / journeys

