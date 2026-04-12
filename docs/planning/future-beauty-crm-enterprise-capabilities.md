# Future Beauty CRM Enterprise Capabilities

Date: 2026-04-12
Branch: `pm/assistant-foundation-week1-backlog`
Status: future reference / not part of current sprint scope

This document preserves strategic future-product context for a **Micro CRM with AI Assistant via WhatsApp for Beauty** (salons, esthetic clinics, eyebrow/lash studios, regional beauty chains, etc.).

The intent is to keep these concepts visible for future roadmap work without forcing them into the current sprint.

---

## Source context to preserve

Excelente contexto. Vamos destrinchar cada um desses termos técnicos aplicados a um **Micro CRM com AI Assistant via WhatsApp para Beleza** (salões, clínicas de estética,设计师 de sobrancelhas, etc.).

A ideia aqui é que você tem um sistema leve (micro), mas com funcionalidades poderosas (enterprise-grade em alguns pontos). O negócio de Beleza tem particularidades: alta taxa de no-show, necessidade de lembretes, venda de produtos e agendamento de serviços recorrentes.

---

### 1. Beauty Journey Builder (Construtor de Jornadas de Beleza)
**O que é:** Um interface *drag-and-drop* (arrasta e solta) para criar automações de marketing e atendimento específicas para o ciclo de vida da cliente de beleza.

**No seu contexto:**
- **Exemplo prático:** Você cria uma jornada "Pós-procedimento de Botox".
    - *Trigger:* Cliente finaliza um agendamento.
    - *Passo 1:* AI envia no WhatsApp: *"Ótimo! Daqui 2 dias, não deite por 4h. Quer lembrete?"*
    - *Passo 2 (condicional):* Se ela responder "sim", agenda um lembrete.
    - *Passo 3 (tempo):* Após 30 dias, envia: *"Hora da manutenção. Quer agendar?"*
- **Diferencial:** O "Beauty" no nome significa que ele já vem com templates prontos: *Recuperação de cliente inativa (90 dias sem ir ao salão)*, *Up-sell de produto pós-química*.

### 2. Campanha Massiva (Massive Campaign)
**O que é:** Envio de mensagens em grande volume (ex: 10k+ contatos) via WhatsApp.

**No seu contexto:**
- **Cuidado:** WhatsApp não é igual e-mail. Campanha massiva no WhatsApp exige *opt-in* explícito e alta relevância para não ser bloqueada como spam.
- **Exemplo prático:** *"Black Friday do Studio Laura: 20% off em todos os procedimentos de cílios. Válido hoje."*
- **Desafio técnico:** Como o CRM é *micro*, essa função precisa usar providers terceiros (Twilio, WATI, Z-API) que gerenciem a taxa de envio (mensagens/segundo) para não derrubar seu número.

### 3. Open/Click Tracking Avançado de Email
**O que é:** Monitorar se o cliente abriu o e-mail e quais links clicou, com dados como geolocalização, dispositivo, horário e heatmap.

**No seu contexto:**
- **Micro CRM + Email?** Sim. Embora o foco seja WhatsApp, o email ainda é crucial para *newsletters* de beleza (antes/depois, tutoriais de maquiagem).
- **Exemplo prático:**
    - Você envia um e-mail com 3 links: [Agendar Corte], [Ver Produtos], [Indicar Amiga].
    - O tracking mostra que 60% das clientes clicaram em [Ver Produtos], mas só 5% em [Agendar Corte].
    - **Ação:** O AI Assistant percebe isso e muda a abordagem no WhatsApp: *"Vi que você gostou dos produtos. Quer que eu mostre o shampoo que usamos no seu último corte?"*

### 4. SLA Engine de Handoff (Engine de Tempo de Transferência)
**O que é:** Regras automáticas que definem *quando* e *como* transferir a conversa do bot (AI) para um humano, baseado em tempo de espera, complexidade ou palavras-chave.

**No seu contexto (crucial para Beleza):**
- **Exemplo de SLA:** "Se o cliente pedir 'cancelar' ou 'reembolso' ou ficar 2 minutos sem resposta do bot → transferir para humano em menos de 30 segundos (SLA de 30s)."
- **Outro trigger:** Se o cliente digitar *"alergia"* ou *"queimadura"* (assunto grave), o SLA engine prioriza transferência imediata para a gerente, ignorando a fila normal.
- **Beleza + SLA:** Em salões, cliente irritada por demora no WhatsApp posta review negativo na hora. Esse motor é vital.

### 5. Múltiplos Providers por Canal
**O que é:** Ter mais de um fornecedor (provider) para o mesmo canal (ex: 2 empresas de WhatsApp + 2 de e-mail + 1 de SMS), com fallback automático.

**No seu contexto:**
- **Por que num micro CRM?** Resiliência. Se a Z-API cair (serviço de WhatsApp), o sistema troca automaticamente para Twilio ou WATI sem parar o atendimento.
- **Exemplo prático:**
    - *Provider A* (mais barato) é usado para campanhas massivas.
    - *Provider B* (mais caro, mas estável) é usado para conversas críticas (agendamento, confirmação de pagamento).
    - *Fallback:* Se B falha, o sistema migra a sessão da cliente para C em < 5 segundos, transparente para a usuária.

### 6. BI Externo Complexo (Complex External BI)
**O que é:** Integração com ferramentas de Business Intelligence (Power BI, Tableau, Looker, Metabase) que rodam fora do seu CRM, consumindo dados brutos para gerar análises pesadas.

**No seu contexto:**
- **O CRM é micro** → ele não processa relatórios pesados internamente. Ele exporta dados em tempo real (via Webhook ou Streaming) para um BI externo.
- **O que esse BI complexo faz para um negócio de Beleza:**
    - **Análise de Lifetime Value (LTV) por procedimento:** Clientes de *Lifting de Pálpebras* gastam 3x mais que clientes de *Limpeza de Pele*.
    - **Previsão de No-Show:** O BI cruza dados de WhatsApp (ex: "cliente que responde com 'rsrs' em vez de confirmar") + histórico de faltas.
    - **Clusterização Avançada:** "Grupo de clientes que compram produtos roxos, moram no bairro X e interagem com stories de unhas de gel" → campanha hiper-mirável.
- **Diferencial:** Você pode conectar esse BI ao seu ERP de salão para saber, em tempo real, *qual assistente de vendas no WhatsApp gera mais receita por hora.*

---

### Resumo Visual (Como tudo se conecta no fluxo real)

```text
Cliente entra via WhatsApp.
    ↓
[AI Assistant] atende. Se ela pedir "Reagendar" → 
    ↓
[SLA Engine] vê que é ação crítica → transfere para humano em 15s.
    ↓
Se for campanha "Promo de Dia das Mães" → 
    ↓
[Múltiplos Providers] escolhe o melhor roteador de WhatsApp para volume.
    ↓
Paralelamente, envia e-mail com [Open/Click Tracking Avançado] para reforçar.
    ↓
Toda ação (agendou, cancelou, perguntou por preço) vira dado bruto.
    ↓
[BI Externo Complexo] (Power BI) gera dashboard: 
"Clientes que interagem com AI às 22h têm 70% mais chance de comprar creme noturno".
    ↓
[Beauty Journey Builder] usa esse insight para criar nova automação.
```

**No fim:** O cliente acha que é um app inteligente. Na verdade, é um micro CRM enxuto, mas com motores de guerra (handoff, multi-provider, BI externo) que só grandes empresas costumam ter. Ideal para franquias de beleza ou redes regionais.

---

## Suggested interpretation for future roadmap

This section is **not** a current implementation commitment. It is a roadmap framing aid.

### Near-future candidate epics
1. Beauty Journey Builder
2. Mass Campaigns with compliance/opt-in controls
3. Advanced Email Open/Click Tracking
4. SLA Engine for Handoff
5. Multi-provider routing and fallback by channel
6. External BI export / streaming layer

### Why preserve this now
This future-oriented framing is useful because the current roadmap already points in related directions:
- communication and measurement work is the foundation for future multi-provider and attribution work
- handoff MVP can later evolve into SLA-based routing
- assistant funnel events can later feed external BI
- automatic confirmations and templates are a stepping stone toward journey building

### Recommendation
Do **not** mix these epics into the current sprint unless explicitly re-scoped. Use them as:
- future roadmap reference
- architecture guardrails
- vocabulary alignment between product, engineering, and operations
