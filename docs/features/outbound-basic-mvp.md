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
  - `assistant_prebook_confirmation`, `assistant_handoff_confirmation` (automação do assistant)
- Variáveis suportadas:
  - `{{customer_name}}`
  - `{{appointment_date}}`, `{{appointment_time}}`
  - `{{service_name}}`, `{{location_name}}`
  - `{{business_name}}`
 - `channel` suportados para templates:
   - `whatsapp`, `email`

### Preview e envio manual
- Preview: `POST /crm/outbound/preview` (renderiza e valida contexto)
- Envio: `POST /crm/outbound/send`
  - **manual send** permanece suportado apenas para `channel=whatsapp`
  - preferencialmente envia via provider (WhatsApp Cloud) se configurado + tenant tiver `whatsapp_accounts` ativo
  - fallback: gera deeplink `wa.me` (envio assistido)
  - guarda histórico em `outbound_messages` (inclui `provider_message_id` quando aplicável)
  - cria interaction `outbound_whatsapp` quando o envio é iniciado com sucesso
- Reenvio: `POST /crm/outbound/{id}/resend` (apenas para mensagens `failed`)

## Use cases (substitui o modelo “send reminder/report” do applandlord)

No TheOne, os casos de uso são modelados como **templates + envio**, em vez de endpoints isolados por ação.

- Booking confirmation → template `booking_confirmation` + `POST /crm/outbound/send`
- Reminder 24h → template `reminder_24h` + `POST /crm/outbound/send`
- Reminder 3h → template `reminder_3h` + `POST /crm/outbound/send`
- Reactivation → template `reactivation` + `POST /crm/outbound/send`

### Sobre “summary/report”

O outbound MVP envia para um **customer** (cliente) como destinatário. Para um report de negócio (para staff):
- MVP (manual): criar um “customer interno” (ex: “Owner”) com o seu telefone e usar um template `internal_followup_support`.
- Próximo passo (fora deste PR): gerar o corpo do relatório (stats) via serviço de reporting/scheduler e chamar `POST /crm/outbound/send` com `final_body`.

### Histórico
- Listagem: `GET /crm/outbound/messages` com filtros por `customer_id`, `template_id`, `type`, `status`
- UI: histórico aparece no customer profile no dashboard.

## Significado de status (importante)
Estados mínimos (compat): `pending`, `sent`, `failed` (e `delivered` quando callbacks chegam).

O campo `status` mantém compatibilidade com o histórico/UI atual (MVP). Interpretação:

- `status=pending`: histórico criado e envio a iniciar (curto; normalmente transita no mesmo request).
- `status=sent`: envio **iniciado** com sucesso:
  - pode ser via provider (WhatsApp Cloud) **ou**
  - pode ser envio manual assistido (deeplink `wa.me`).
- `status=failed`: falhou ao iniciar:
  - pré-validação (ex: cliente sem telefone válido) **ou**
  - tentativa provider-backed falhou (neste caso pode existir `whatsapp_url` para envio manual).

Para tracking real, usar `delivery_status`:

- `delivery_status=queued`: criado e aguardando envio provider-backed.
- `delivery_status=accepted`: provider aceitou o envio e devolveu `provider_message_id`.
- `delivery_status=delivered/read`: provider confirmou entrega/leitura via callback.
- `delivery_status=failed`: falhou (preparação ou provider).
- `delivery_status=unconfirmed`: fallback deeplink; não existe confirmação de entrega do provider.

## Resposta do `POST /crm/outbound/send` (como ler)

Campos úteis para UI/produto:
- `mode`:
  - `provider`: o provider aceitou o envio (aguarda callbacks).
  - `deeplink`: envio manual assistido (usar `whatsapp_url`).
  - `none`: não há envio possível (erro).
- `requires_user_action`:
  - `true` quando o usuário precisa abrir o link do WhatsApp para enviar.
- `idempotency_replay`:
  - `true` quando o servidor devolve o mesmo envio por replay de `Idempotency-Key`.
- `duplicate_prevented`:
  - `true` quando o servidor detecta clique duplo (mesmo corpo, janela curta) e devolve a mensagem existente.

Notas:
- `ok=true` significa “o fluxo gerou um resultado utilizável” (ex: provider aceitou ou deeplink foi gerado).
- Em falha do provider, `ok` pode ser `false` mas `mode=deeplink` pode estar presente para permitir envio manual.

## Interactions
Quando uma mensagem outbound fica com `status=sent`, é criada uma interaction no CRM:
- `type`: `outbound_whatsapp`
- `content`: corpo final renderizado/enviado

## Callbacks de entrega (provider-backed)

- Endpoint principal (Meta Webhooks): `POST /messaging/webhook`
  - mesmo webhook usado para inbound; o TheOne extrai `statuses[]` e processa o lifecycle de entrega.
  - sem tenant header; tenant é resolvido via `whatsapp_accounts` (`provider + phone_number_id`).
- Endpoint normalizado (útil para testes/relay): `POST /messaging/delivery`
  - payload interno/normalizado (não é o payload original do Meta).
  - sem tenant header; tenant é resolvido por `phone_number_id`.
- Dedupe: por `(tenant_id, provider, external_event_id)` em `outbound_delivery_events`
- Atualiza `outbound_messages.delivery_status` e timestamps (`delivered_at`, `failed_at`)

Variáveis de ambiente relevantes:
- `WHATSAPP_WEBHOOK_SECRET` (Meta App Secret; verificação de assinatura `X-Hub-Signature-256` nos callbacks)
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (handshake GET de verificação do webhook)
- `WHATSAPP_CLOUD_ACCESS_TOKEN`, `WHATSAPP_CLOUD_API_VERSION`, `WHATSAPP_CLOUD_TIMEOUT_SECONDS` (envio via provider)

## Fora de scope neste PR
- automações genéricas (journeys/campanhas). Apenas confirmações automáticas do assistant.
- múltiplos canais no envio manual (UI)
- campanhas massivas / segmentação / journeys

> Nota: automações do assistant (confirmações automáticas) são documentadas em `docs/features/assistant-automatic-confirmations.md`.
