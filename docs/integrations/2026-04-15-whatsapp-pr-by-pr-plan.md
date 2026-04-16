# TheOne — WhatsApp Meta Plan dividido PR por PR

Data: 2026-04-15

Baseado em:
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`

## 1) Objetivo deste documento

Este documento pega no guia de replicação WhatsApp Meta e transforma-o em execução **PR por PR** dentro do `theone`.

O objetivo aqui não é copiar o `applandlord`.
O objetivo é:
- confirmar e endurecer o que o `theone` já tem;
- expor melhor a experiência de produto;
- adicionar os casos de uso que fazem sentido;
- tornar WhatsApp um canal visível e confiável dentro da app.

---

## 2) Princípio orientador

O `theone` já está à frente do `applandlord` em arquitetura WhatsApp porque já tem:
- inbound webhook;
- assinatura HMAC;
- routing por tenant;
- outbound provider-backed;
- fallback deeplink;
- histórico;
- delivery lifecycle.

Portanto, as PRs certas são:
1. validar e consolidar a base;
2. melhorar UX/admin;
3. expor casos de uso de produto;
4. trazer estados e pendências para a experiência principal;
5. endurecer a operação.

---

# PR 1 — Setup, docs e validação ponta-a-ponta da integração Meta

## Objetivo
Garantir que a integração atual está realmente configurável, documentada e testável em ambiente real.

## Scope
- docs de setup
- validação de env vars
- clareza do fluxo outbound + webhook verification
- checklist operacional mínimo

## Ficheiros principais
- `.env.example`
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`
- `docs/features/outbound-basic-mvp.md`
- `app/http/routes/messaging.py`
- `modules/messaging/providers/meta_whatsapp_cloud.py`
- `modules/messaging/providers/meta_cloud.py`
- `tests/api/test_inbound_webhook.py`
- `tests/api/test_outbound_provider_lifecycle_api.py`

## Checklist
- [ ] rever `.env.example` e confirmar nomenclatura final
- [ ] documentar claramente:
  - `WHATSAPP_WEBHOOK_SECRET`
  - `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
  - `WHATSAPP_CLOUD_ACCESS_TOKEN`
  - `WHATSAPP_CLOUD_API_VERSION`
  - `WHATSAPP_CLOUD_TIMEOUT_SECONDS`
- [ ] documentar fluxo GET verify webhook
- [ ] documentar fluxo POST webhook inbound
- [ ] documentar fluxo outbound provider-backed
- [ ] documentar fallback para `wa.me`
- [ ] rever testes existentes e cobrir setup/fluxo mínimo
- [ ] deixar uma checklist manual de validação end-to-end

## Critérios de aceitação
- qualquer pessoa da equipa percebe como configurar Meta Cloud API no `theone`
- os nomes de env vars ficam consistentes
- há uma forma clara de validar webhook verify, outbound send e delivery callback

---

# PR 2 — Melhorar a página admin de ligação WhatsApp

## Objetivo
Transformar a página técnica de `whatsapp-accounts` numa UI mais orientada a produto e operação.

## Scope
- melhorar admin page
- tornar o mapping por tenant mais claro
- reduzir linguagem técnica crua

## Ficheiros principais
- `frontend/app/dashboard/admin/whatsapp-accounts/page.tsx`
- `app/http/routes/messaging.py`
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`

## Checklist
- [ ] mudar framing da página de “form técnico” para “connect WhatsApp number”
- [ ] explicar o que é `phone_number_id`
- [ ] mostrar provider atual de forma mais clara
- [ ] mostrar estado atual da ligação
- [ ] preparar espaço visual para:
  - connection status
  - webhook verification status
  - last delivery callback received
- [ ] melhorar estados de sucesso/erro
- [ ] manter compatibilidade com endpoint atual de criação

## Critérios de aceitação
- um admin percebe como ligar uma conta sem ler o código
- a página já parece parte do produto, não só um painel interno bruto

---

# PR 3 — Validar e productizar outbound send simples

## Objetivo
Pegar no equivalente conceptual do `lib/whatsapp.ts` do `applandlord` e garantir que no `theone` isso está sólido, claro e facilmente acionável.

## Scope
- revisão do fluxo `POST /crm/outbound/send`
- melhoria de mensagens/notes devolvidas
- preparação para uso simples por customer/appointment

## Ficheiros principais
- `app/http/routes/outbound.py`
- `modules/messaging/providers/meta_whatsapp_cloud.py`
- `docs/features/outbound-basic-mvp.md`
- `tests/api/test_outbound_provider_lifecycle_api.py`

## Checklist
- [ ] rever o fluxo provider-backed + fallback
- [ ] garantir que erros devolvem mensagens úteis
- [ ] garantir que response deixa claro quando foi:
  - provider send
  - fallback deeplink
  - failure
- [ ] rever idempotency e comportamento de double-send
- [ ] documentar claramente o que significa `sent`, `accepted`, `failed`, `unconfirmed`
- [ ] garantir que o histórico outbound fica consistente

## Critérios de aceitação
- o fluxo outbound simples está funcional e inteligível
- o utilizador/engenharia consegue perceber o resultado do envio sem ler infra

---

# PR 4 — Templates default e casos de uso equivalentes ao applandlord

## Objetivo
Subir os casos de uso que no `applandlord` eram simples API routes para features reais do `theone`.

## Scope
- templates default
- reminders
- booking confirmation
- reactivation
- daily/weekly summary action

## Ficheiros principais
- `app/http/routes/outbound.py`
- `frontend/app/dashboard/outbound/templates/...` se aplicável
- `docs/features/outbound-basic-mvp.md`
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`
- `tests/api/test_outbound_provider_lifecycle_api.py`

## Checklist
- [ ] garantir templates default para:
  - `booking_confirmation`
  - `reminder_24h`
  - `reminder_3h`
  - `reactivation`
- [ ] definir ação de summary/report do negócio
- [ ] evitar criar endpoint hacky fora do domínio quando já existe outbound infra
- [ ] documentar como esses casos substituem:
  - send reminder
  - send report
- [ ] garantir que podem ser usados a partir do CRM

## Critérios de aceitação
- o `theone` já cobre os principais casos de uso “tipo applandlord” sem copiar a implementação dele

---

# PR 5 — Surface de delivery lifecycle na UI

## Objetivo
Fazer os estados de entrega WhatsApp aparecerem onde geram valor para o produto.

## Scope
- mostrar `accepted`, `delivered`, `read`, `failed`, `unconfirmed`
- integrar isso no histórico certo

## Ficheiros principais
- `frontend/app/dashboard/customers/...` (onde existir histórico/outbound)
- `frontend/app/dashboard/page.tsx`
- `app/http/routes/outbound.py`
- `docs/features/outbound-basic-mvp.md`

## Checklist
- [ ] escolher superfícies certas para mostrar delivery state
- [ ] mostrar labels/status de forma compreensível
- [ ] não misturar `status` legado com `delivery_status` sem contexto
- [ ] melhorar mapping entre backend e UI
- [ ] documentar claramente o significado de cada estado

## Critérios de aceitação
- o utilizador vê se a mensagem foi só iniciada, aceite, entregue, lida ou falhou
- a UI comunica valor real da integração provider-backed

---

# PR 6 — Inbox summary e pending replies

## Objetivo
Fechar o loop de comunicação: não basta enviar; é preciso ver o que ficou por responder.

## Scope
- pending replies
- unread conversations
- última inbound por conversa
- surface na home ou inbox summary

## Ficheiros principais
- `app/http/routes/dashboard.py`
- `app/http/routes/messaging.py`
- `frontend/app/dashboard/page.tsx`
- `frontend/components/dashboard/PendingInboxCard.tsx`
- `frontend/app/dashboard/inbox/page.tsx` se existir/criar
- `frontend/lib/contracts/inbox.ts` se necessário

## Checklist
- [ ] definir “awaiting reply” oficialmente
- [ ] calcular unread/awaiting reply no backend
- [ ] mostrar resumo na home
- [ ] criar/ligar entry point para inbox
- [ ] alinhar isto com a definição do roadmap principal

## Critérios de aceitação
- a home mostra pendência comunicacional real
- WhatsApp deixa de ser só outbound e passa a ser canal operacional

---

# PR 7 — Botões e ações rápidas de WhatsApp no CRM

## Objetivo
Levar o WhatsApp para perto da operação do dia-a-dia, sem obrigar o utilizador a navegar por templates toda a hora.

## Scope
- quick actions em customer/appointment
- “send WhatsApp” simples
- atalhos para reminder/follow-up/confirmation

## Ficheiros principais
- `frontend/app/dashboard/customers/...`
- `frontend/app/dashboard/appointments/...`
- `frontend/app/dashboard/page.tsx`
- `app/http/routes/outbound.py`

## Checklist
- [ ] adicionar botão “Send WhatsApp” no lugar certo
- [ ] adicionar shortcut para reminder em appointment
- [ ] adicionar shortcut para booking confirmation
- [ ] usar infraestrutura existente de outbound/templates
- [ ] não duplicar fluxos desnecessários

## Critérios de aceitação
- o utilizador consegue usar WhatsApp no CRM sem parecer um fluxo escondido ou técnico

---

# PR 8 — Report diário/semanal por WhatsApp como feature de produto

## Objetivo
Criar o equivalente limpo do `app/api/reports/whatsapp/route.ts` do `applandlord`, mas do jeito certo no `theone`.

## Scope
- business summary/report action
- cálculo de métricas
- envio para número admin configurado

## Ficheiros principais
- `app/http/routes/outbound.py` ou nova rota de reports/outbound do domínio
- `app/http/routes/dashboard.py`
- `modules/...` de analytics/reporting se necessário
- `docs/integrations/2026-04-15-whatsapp-meta-replication-guide.md`
- `tests/...` relevantes

## Checklist
- [ ] definir o payload/report format
- [ ] calcular métricas certas do tenant
- [ ] enviar para número admin definido nas settings
- [ ] documentar periodicidade manual e futura automação
- [ ] manter consistência com outbound infra existente

## Critérios de aceitação
- o `theone` ganha uma feature real de report por WhatsApp, sem hacks isolados

---

# PR 9 — Endurecimento técnico antes de escalar WhatsApp

## Objetivo
Tratar os bloqueios que podem partir a operação WhatsApp em produção.

## Scope
- segurança
- RBAC mínimo
- observabilidade
- pontos críticos do inbound/tenant lookup

## Ficheiros principais
- `docs/audit/2026-04-09-technical-audit.md`
- `app/http/routes/messaging.py`
- `modules/messaging/repo/sql.py`
- `core/observability/...`
- `app/http/routes/billing.py`
- peças relacionadas com RBAC/tenancy

## Checklist
- [ ] rever segredos/versionamento
- [ ] tratar risco de `billing in-memory`
- [ ] tratar conflito de RLS com resolução de tenant em inbound
- [ ] adicionar RBAC mínimo em ações admin sensíveis
- [ ] adicionar logging/métricas mínimas para inbound/outbound/delivery

## Critérios de aceitação
- a integração WhatsApp deixa de assentar em base operacional frágil
- há rastreabilidade mínima em produção

---

## 3) Ordem recomendada de merge

1. PR 1 — Setup, docs e validação ponta-a-ponta da integração Meta
2. PR 2 — Melhorar a página admin de ligação WhatsApp
3. PR 3 — Validar e productizar outbound send simples
4. PR 4 — Templates default e casos de uso equivalentes ao applandlord
5. PR 5 — Surface de delivery lifecycle na UI
6. PR 6 — Inbox summary e pending replies
7. PR 7 — Botões e ações rápidas de WhatsApp no CRM
8. PR 8 — Report diário/semanal por WhatsApp como feature de produto
9. PR 9 — Endurecimento técnico antes de escalar WhatsApp

---

## 4) Ordem mínima se quiseres avançar mais rápido

Se quiseres resolver primeiro o essencial do canal WhatsApp no produto:

1. PR 1
2. PR 2
3. PR 3
4. PR 5
5. PR 6

Esse conjunto já transforma o WhatsApp numa capability visível e utilizável no `theone`.

---

## 5) Conclusão prática

A divisão correta do guia em PRs não é “copiar ficheiros do applandlord”.

É esta sequência:
- consolidar infra
- melhorar ligação/admin UX
- tornar outbound claro
- subir casos de uso de negócio
- mostrar estados de entrega
- fechar loop com inbox/pending replies
- endurecer produção

É isso que faz o `theone` aproveitar a vantagem arquitetural que já tem.
