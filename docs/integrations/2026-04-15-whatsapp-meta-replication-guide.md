# WhatsApp Meta Guide — `applandlord` vs `theone`

Data: 2026-04-15

## 1) Conclusão principal

Depois de inspecionar o histórico do repositório `viniciusandrade95/applandlord`, a conclusão importante é esta:

**o `applandlord` tem uma integração WhatsApp mais simples e mais limitada do que a que o `theone` já possui hoje.**

Ou seja, o objetivo não deve ser “copiar o WhatsApp do `applandlord` para o `theone`”.
O objetivo certo é:

**confirmar como o `applandlord` faz o envio outbound simples e garantir que o `theone` já cobre isso — ou adaptar apenas o que fizer sentido de produto/UI.**

---

## 2) O que o `applandlord` fez exatamente

O `applandlord` introduziu a integração em 4 peças principais no histórico:

### 2.1 Helper simples de envio
Commit:
- `aad68b67f3595751fe888435393b900a645dfb7f`
- URL: <https://github.com/viniciusandrade95/applandlord/commit/aad68b67f3595751fe888435393b900a645dfb7f>

Esse commit adiciona `lib/whatsapp.ts` com uma função `sendTextMessage(to, body)` que:
- lê `WHATSAPP_TOKEN`
- lê `WHATSAPP_PHONE_NUMBER_ID`
- faz `POST` para `https://graph.facebook.com/v19.0/{phoneNumberId}/messages`
- envia mensagem `type: text`
- devolve o JSON da Meta

Em termos de arquitetura, é um helper **outbound-only**.
Não trata inbound webhook, multi-tenant, histórico, delivery lifecycle, nem routing por conta.

### 2.2 API route para reminder
Commit:
- `bb67357b5d9f443e06c576c82592384aa600b7c6`
- URL: <https://github.com/viniciusandrade95/applandlord/commit/bb67357b5d9f443e06c576c82592384aa600b7c6>

Foi criada a rota `app/api/whatsapp/send-reminder/route.ts` que:
- recebe `tenantId`
- faz lookup do tenant no Prisma
- monta uma mensagem de lembrete de renda
- chama `sendTextMessage`

Isto é útil como padrão mental:
**dados do negócio -> compor mensagem -> enviar via helper**.

### 2.3 Envio de relatório por WhatsApp
Commit:
- `ce723a9e54900e3df421b9039c6877ee878a0e2b`
- URL: <https://github.com/viniciusandrade95/applandlord/commit/ce723a9e54900e3df421b9039c6877ee878a0e2b>

Foi criada a rota `app/api/reports/whatsapp/route.ts` que:
- conta tenants
- conta overdue
- soma renda mensal esperada
- envia um relatório WhatsApp para `LANDLORD_PHONE`

### 2.4 Setup doc mínimo
Commit:
- `fbad089f59859810797b7dd0202481b33ca874f2`
- URL: <https://github.com/viniciusandrade95/applandlord/commit/fbad089f59859810797b7dd0202481b33ca874f2>

Define apenas:
- `WHATSAPP_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- endpoint de teste para reminder

---

## 3) Em resumo: que tipo de integração existe no `applandlord`

### O que existe
- envio outbound simples
- mensagem de texto simples
- Meta Graph API
- uso de env vars
- trigger por API route

### O que não existe
- inbound webhook operacional
- verificação de assinatura HMAC
- múltiplos tenants roteados por `phone_number_id`
- fila/worker
- lifecycle de entrega persistido
- histórico unificado de outbound/inbound
- templates avançados por tenant
- fallback controlado
- account mapping admin

---

## 4) O que o `theone` já tem hoje

O `theone` já cobre várias camadas que o `applandlord` não cobre.

### 4.1 Inbound webhook Meta
- rota de webhook e parsing de eventos: [`../../app/http/routes/messaging.py`](../../app/http/routes/messaging.py)
- verificação HMAC: [`../../modules/messaging/providers/meta_cloud.py`](../../modules/messaging/providers/meta_cloud.py)

### 4.2 Config de webhook + provider-backed outbound
- envs previstos no `.env.example`: [`../../.env.example`](../../.env.example)
- inclui:
  - `WHATSAPP_WEBHOOK_SECRET`
  - `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
  - `WHATSAPP_CLOUD_ACCESS_TOKEN`
  - `WHATSAPP_CLOUD_API_VERSION`
  - `WHATSAPP_CLOUD_TIMEOUT_SECONDS`

### 4.3 Sender outbound provider-backed
- sender Meta WhatsApp Cloud já implementado: [`../../modules/messaging/providers/meta_whatsapp_cloud.py`](../../modules/messaging/providers/meta_whatsapp_cloud.py)

### 4.4 Fluxo outbound completo
- templates
- preview
- envio manual assistido via `wa.me`
- envio provider-backed quando configurado
- histórico
- fallback
- delivery callbacks

Tudo isto já está em: [`../../app/http/routes/outbound.py`](../../app/http/routes/outbound.py)

### 4.5 Documentação interna do próprio repo
- outbound MVP: [`../features/outbound-basic-mvp.md`](../features/outbound-basic-mvp.md)
- catálogo funcional: [`../audit/2026-04-09-functional-catalog.md`](../audit/2026-04-09-functional-catalog.md)
- auditoria técnica: [`../audit/2026-04-09-technical-audit.md`](../audit/2026-04-09-technical-audit.md)

---

## 5) Então o que realmente precisas de “replicar”?

Na prática, precisas replicar apenas **a intenção de produto**, não a implementação literal.

A intenção do `applandlord` era:
1. ter um helper simples para enviar WhatsApp;
2. usar dados do sistema para compor mensagens úteis;
3. disparar esses envios por endpoints/ações concretas.

O `theone` já está além disso.

Logo, a replicação correta dentro do `theone` é:
- confirmar configuração real da Meta;
- ligar essa capacidade às ações de produto certas;
- simplificar a UI para o dono do negócio;
- expor casos de uso como reminders, reports e follow-ups na superfície do produto.

---

## 6) Step by step recomendado para o `theone`

## Step 1 — Confirmar qual modo queres suportar
Decisão de produto:
- **Modo A:** envio manual assistido (deeplink)
- **Modo B:** envio provider-backed real via Meta Cloud API
- **Modo C:** ambos, com fallback

O `theone` já foi desenhado para **Modo C**.

### Recomendação
Manter o desenho atual do `theone`:
- provider-backed quando configurado;
- deeplink fallback quando não estiver configurado ou quando falhar.

---

## Step 2 — Confirmar variáveis de ambiente reais
Usar o padrão já previsto no `theone`:
- `WHATSAPP_WEBHOOK_SECRET`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_CLOUD_ACCESS_TOKEN`
- `WHATSAPP_CLOUD_API_VERSION`
- `WHATSAPP_CLOUD_TIMEOUT_SECONDS`

Não introduzir `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID` como padrão novo só porque o `applandlord` fez assim.

### Motivo
O `theone` já tem uma convenção mais completa e mais coerente.

---

## Step 3 — Confirmar o mapping de conta WhatsApp por tenant
No `theone`, o tenant resolve-se por `provider + phone_number_id`.
Isto é muito melhor do que um helper global sem contexto de tenant.

Tarefa prática:
- garantir que o admin configure `phone_number_id` na página existente:
  - [`../../frontend/app/dashboard/admin/whatsapp-accounts/page.tsx`](../../frontend/app/dashboard/admin/whatsapp-accounts/page.tsx)

### Melhoria sugerida
Esta página ainda está demasiado técnica.
Transformá-la numa UI mais orientada a produto:
- “Connect WhatsApp number”
- “Connection status”
- “Meta phone number ID”
- “Webhook verification status”
- “Last delivery callback received”

---

## Step 4 — Validar o envio outbound simples
O equivalente conceptual de `lib/whatsapp.ts` no `theone` já existe em:
- [`../../modules/messaging/providers/meta_whatsapp_cloud.py`](../../modules/messaging/providers/meta_whatsapp_cloud.py)

Tens de validar este fluxo ponta-a-ponta:
1. tenant com `whatsapp_account` ativo
2. `WHATSAPP_CLOUD_ACCESS_TOKEN` configurado
3. customer com telefone válido
4. envio de template ou final body via `POST /crm/outbound/send`
5. Meta devolve `provider_message_id`
6. status fica `accepted/sent`

Isto é o verdadeiro equivalente do `applandlord`, só que melhor estruturado.

---

## Step 5 — Expor os casos de uso que no `applandlord` estavam em API routes simples
No `applandlord`, os casos de uso eram:
- send reminder
- send report

No `theone`, o ideal é não criar rotas avulsas sem modelo.
O certo é encaixar estes casos em serviços/ações do domínio.

### 5.1 Reminder de appointment
Implementar/usar template do tipo:
- `reminder_24h`
- `reminder_3h`

A infraestrutura de templates já existe no outbound.

### 5.2 Booking confirmation
Usar:
- `booking_confirmation`

### 5.3 Reactivation
Usar:
- `reactivation`

### 5.4 Daily / weekly business summary
Se quiseres o equivalente do report do `applandlord`, criar uma ação específica como:
- `POST /crm/outbound/reports/daily-summary`

Essa ação deve:
- calcular métricas do tenant
- gerar corpo
- enviar para número admin definido nas settings do negócio

Isto deve ser modelado como feature do produto, não como hack isolado.

---

## Step 6 — Ligar delivery lifecycle à UI
O `applandlord` só envia e pronto.
O `theone` já pensa em lifecycle.

Tens de tornar isso visível na interface:
- sent
- accepted
- delivered
- read
- failed

### Onde mostrar
- customer profile
- outbound history
- eventualmente na conversation/inbox

Sem isto, a infra existe mas o produto não comunica valor ao utilizador.

---

## Step 7 — Confirmar inbound e reply loop
Se o objetivo é comunicação real por WhatsApp, não basta enviar.

É preciso fechar o loop:
- cliente responde
- inbound webhook entra
- conversa atualiza
- equipa vê mensagem por responder
- home mostra pendência

O `theone` já tem boa parte desta base técnica. O trabalho agora é de produto e UI.

---

## Step 8 — Endurecer a parte técnica antes de depender disto em produção
A auditoria do repo já identificou pontos que afetam diretamente esta integração:
- segredos no repo;
- billing in-memory;
- RLS vs inbound account lookup;
- falta de RBAC;
- falta de observabilidade.

Ver: [`../audit/2026-04-09-technical-audit.md`](../audit/2026-04-09-technical-audit.md)

### Regra prática
Antes de promover WhatsApp a canal central do produto:
- corrigir configuração/segurança
- adicionar métricas/logs
- garantir comportamento determinístico API/worker

---

## 7) Implementação recomendada por ordem

## Fase A — Confirmar o que já existe
Checklist:
- [ ] `.env` real com creds corretas da Meta
- [ ] `whatsapp_accounts` configurado por tenant
- [ ] teste manual de `POST /crm/outbound/send`
- [ ] callback de delivery validado
- [ ] webhook GET verification validado

## Fase B — Productize the experience
Checklist:
- [ ] UI melhor para ligar conta WhatsApp
- [ ] templates default por tenant
- [ ] botão simples “send WhatsApp” em customer / appointment
- [ ] histórico de entrega visível

## Fase C — Casos de uso equivalentes ao `applandlord`
Checklist:
- [ ] reminder manual
- [ ] reminder automático
- [ ] report diário/semanal
- [ ] follow-up pós-serviço
- [ ] reactivation

## Fase D — Surface na home
Checklist:
- [ ] pending messages
- [ ] pending confirmations
- [ ] failed deliveries
- [ ] unread conversations

---

## 8) O que eu faria, objetivamente

Se a pergunta é “como replico aquilo que foi feito no `applandlord` no `theone`?”, a minha resposta honesta é:

### Não copies a implementação do `applandlord`
Porque ela é mais simples e mais fraca do que a do `theone`.

### Faz isto em vez disso
1. usa o outbound provider do `theone`
2. valida a configuração Meta real
3. cria flows de produto equivalentes aos do `applandlord`
4. melhora a UI/admin setup
5. traz delivery status e pending replies para a experiência principal

---

## 9) Tradução direta do `applandlord` para `theone`

### `applandlord`: `lib/whatsapp.ts`
### `theone`: `modules/messaging/providers/meta_whatsapp_cloud.py`

### `applandlord`: `app/api/whatsapp/send-reminder/route.ts`
### `theone`: usar `POST /crm/outbound/send` + templates + eventual action de reminder

### `applandlord`: `app/api/reports/whatsapp/route.ts`
### `theone`: criar action de summary/report usando o mesmo outbound infra do CRM

### `applandlord`: `WHATSAPP_SETUP.md`
### `theone`: consolidar setup em docs + admin connection UI + `.env.example`

---

## 10) Conclusão

O `applandlord` prova uma coisa útil:
**mandar uma mensagem de texto via Meta é simples.**

Mas o `theone` já evoluiu para um desenho mais sério:
- multi-tenant
- inbound
- outbound com provider
- templates
- history
- delivery lifecycle
- fallback

Portanto, o passo certo não é importar código do `applandlord`.
É usar o `applandlord` só como confirmação conceptual e continuar a investir no desenho mais robusto que o `theone` já tem.
