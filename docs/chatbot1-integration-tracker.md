# Tracker Operacional — Integração `theone` + `chatbot1`

## Objetivo do tracker
Este ficheiro serve como quadro operativo inicial da integração entre `theone` e `chatbot1`.

Deve ser usado para:
- acompanhar progresso
- explicitar owners
- identificar bloqueios
- alinhar prioridades
- manter foco no scope da release inicial

---

## Regras de utilização

### Estados sugeridos
- `todo`
- `in_progress`
- `blocked`
- `review`
- `done`

### Prioridades sugeridas
- `P0` — crítico para a release inicial
- `P1` — importante para a release inicial, mas não bloqueia o arranque
- `P2` — importante para robustez / pós-release inicial

### Owners sugeridos
- `senior_engineer`
- `fullstack`
- `product_ops`
- `shared`

---

## Visão rápida

### Objetivo da release inicial
Entregar uma integração interna no dashboard do `theone` que permita:
- conversa com o assistente
- FAQ útil
- handoff
- prebooking / booking assistido controlado
- rastreabilidade ponta a ponta

### Fora de scope inicial
- WhatsApp completo
- canal público conversacional completo
- cancelamento/remarcação avançados automatizados
- rollout multi-canal

### Estado atual local
- A fase de testes do chatbot está fechada; não reabrir sidequest debugging nem testes de fluxo conversacional.
- Último run verde: `docs/test_runs/sidequest_local_20260422_223508`
- Signoff: `/home/vinicius/system-audit/workspace/final_test_signoff_20260422_225617/FINAL_STATUS.txt`
- Relatório de estado: `/home/vinicius/system-audit/workspace/PROJECT_STATE_REPORT.md`
- Os resultados canônicos do autonomous tester são `autonomous/rolling_summary.json` e `autonomous/top_failures.md`; `autonomous_tester.txt` pode ficar vazio.
- A antiga pendência de 5 testes 401 em `tests/api/test_assistant_workflows_reschedule.py` está resolvida/localmente verde.
- Próximo foco: consolidação do ritual local, robustez curta e piloto interno controlado.

---

## Board de trabalho

| ID | Task | Prioridade | Owner | Estado | Dependências | Bloqueios | Notes |
|---|---|---|---|---|---|---|---|
| T0.1 | Inventariar endpoints reais do backend do `theone` | P0 | senior_engineer | done | - | - | Inventário coberto pelos docs e pelo código de rotas atuais |
| T0.2 | Fechar scope da release 1 | P0 | product_ops | done | - | - | Scope permanece dashboard-first/local; sem rollout multi-canal |
| T0.3 | Validar contrato técnico inicial | P0 | senior_engineer | done | T0.1 | - | Contrato validado para a integração local atual |
| T1.1 | Disponibilizar `chatbot1` em ambiente local controlado | P0 | senior_engineer | done | T0.3 | - | Serviço local com `/health`, `/message`, `/reset`; sem trabalho de deploy |
| T1.2 | Criar `/api/chatbot/message` no `theone` | P0 | fullstack | done | T1.1, T0.3 | - | Proxy server-side implementado |
| T1.3 | Criar `/api/chatbot/reset` no `theone` | P0 | fullstack | done | T1.1, T0.3 | - | Reset de sessão/conversa implementado |
| T1.4 | Definir/persistir modelo de `conversation_id` | P0 | senior_engineer | done | T0.3 | - | Mapeamento `conversation_id` <-> `chatbot_session_id` implementado |
| T1.5 | Criar UI inicial do assistente no dashboard | P0 | fullstack | todo | T1.2, T1.3, T1.4 | - | Não reavaliado neste cleanup |
| T1.6 | Propagar `trace_id` ponta a ponta | P0 | senior_engineer | done | T1.1, T1.2 | - | Trace propagado nos proxies e connector local |
| T1.7 | QA local da integração mínima | P0 | product_ops | done | T1.5, T1.6 | - | Fechado por sidequest/local evidence; não reabrir |
| T2.1 | Definir endpoints operacionais do `theone` para assistant actions | P0 | senior_engineer | done | T0.1 | - | `prebook` e rotas internas de workflow existem; quote/consult seguem como evolução |
| T2.2 | Criar `TheOneConnector` no `chatbot1` | P0 | senior_engineer | done | T2.1 | - | Connector implementado |
| T2.3 | Ligar workflow de prebooking ao CRM real | P0 | senior_engineer | done | T2.2 | - | Prebooking local validado contra `/crm/assistant/prebook` |
| T2.4 | Ligar handoff real ao `theone` | P0 | senior_engineer | todo | T2.2 | - | Handoff visível/operável dentro do CRM |
| T2.5 | Tornar resultado operacional visível no `theone` | P0 | fullstack | done | T2.3, T2.4 | - | Resultado operacional de prebooking validado localmente; handoff segue separado |
| T2.6 | Implementar idempotência mínima nas ações operacionais | P1 | senior_engineer | done | T2.2 | - | Idempotência mínima de prebooking implementada |
| T2.7 | QA local de workflows reais | P0 | product_ops | done | T2.5, T2.6 | - | Hybrid/autonomous verdes; fase de teste fechada |
| T3.1 | Decidir estratégia de grounding inicial | P1 | senior_engineer | todo | T0.1 | - | Sync controlado vs provider remoto vs híbrido |
| T3.2 | Mapear `theone` -> profile/facts/services/professionals | P1 | senior_engineer | todo | T3.1 | - | Estruturar dados consumíveis pelo `chatbot1` |
| T3.3 | Preparar FAQ e policies iniciais do tenant piloto | P1 | product_ops | todo | T3.1 | - | Horário, morada, pagamentos, políticas |
| T3.4 | Ligar grounding do tenant piloto ao `chatbot1` | P1 | senior_engineer | todo | T3.2, T3.3 | - | Primeiro grounding real verificável |
| T3.5 | Validar qualidade das respostas FAQ | P1 | product_ops | todo | T3.4 | - | Garantir que o assistente não responde de forma genérica demais |
| T4.1 | Instrumentar métricas mínimas | P1 | senior_engineer | todo | T1.6 | - | Conversas, erro, latência, handoff, no_evidence |
| T4.2 | Selecionar tenant piloto | P0 | product_ops | todo | T0.2 | - | Escolher tenant com dados suficientes |
| T4.3 | Executar piloto interno controlado | P0 | shared | todo | T2.7, T3.5, T4.2 | - | Release interna controlada |
| T4.4 | Consolidar feedback e bugs do piloto | P0 | product_ops | todo | T4.3 | - | Classificar severidade e impacto |
| T4.5 | Corrigir blockers da release inicial | P0 | shared | todo | T4.4 | - | Apenas blockers e regressões críticas |
| T4.6 | Decidir expansão para booking público / WhatsApp | P2 | shared | todo | T4.5 | - | Não decidir antes do piloto interno fechar bem |

---

## Quadro por fase

### Fase 0 — Foundation & Discovery
**Objetivo:** fechar arquitetura, scope e realidade do backend do `theone`

**Tasks:**
- T0.1
- T0.2
- T0.3

**Meta de saída da fase:**
- contrato v1 fechado
- scope fechado
- inventário do backend pronto

---

### Fase 1 — Integração mínima segura
**Objetivo:** falar com o assistente no dashboard do `theone`

**Tasks:**
- T1.1
- T1.2
- T1.3
- T1.4
- T1.5
- T1.6
- T1.7

**Meta de saída da fase:**
- dashboard assistant funcional
- conversa persistida
- tracing inicial ativo

---

### Fase 2 — Execução operacional real
**Objetivo:** trocar a execução fake por integração real com o `theone`

**Tasks:**
- T2.1
- T2.2
- T2.3
- T2.4
- T2.5
- T2.6
- T2.7

**Meta de saída da fase:**
- pelo menos 1 workflow real a funcionar ponta a ponta
- efeito operacional verificável no CRM

---

### Fase 3 — Grounding por tenant
**Objetivo:** fazer o assistente responder com contexto real do negócio

**Tasks:**
- T3.1
- T3.2
- T3.3
- T3.4
- T3.5

**Meta de saída da fase:**
- tenant piloto com grounding verificável
- FAQ úteis e específicas

---

### Fase 4 — Hardening e rollout
**Objetivo:** lançar de forma controlada e com feedback real

**Tasks:**
- T4.1
- T4.2
- T4.3
- T4.4
- T4.5
- T4.6

**Meta de saída da fase:**
- piloto interno concluído
- blockers corrigidos
- decisão informada sobre expansão

---

## Milestones sugeridas

| Milestone | Critério |
|---|---|
| M1 — Foundation ready | T0.1 + T0.2 + T0.3 concluídas |
| M2 — Assistant visible in dashboard | T1.1 até T1.7 concluídas |
| M3 — First real workflow live | T2.1 até T2.7 concluídas |
| M4 — Tenant grounded | T3.1 até T3.5 concluídas |
| M5 — Pilot complete | T4.1 até T4.5 concluídas |

---

## Riscos ativos

| ID | Risco | Impacto | Mitigação | Owner |
|---|---|---|---|---|
| R1 | Backend real do `theone` não expõe tudo o que o frontend sugere | Alto | Fazer T0.1 antes de desenhar demais | senior_engineer |
| R2 | Scope creep para WhatsApp/public chat cedo demais | Alto | Dashboard-first e release 1 limitada | product_ops |
| R3 | `FakeCalendarConnector` voltar a ser assumido como centro do fluxo local | Médio | Manter docs alinhadas com `TheOneConnector` e prebooking real local | senior_engineer |
| R4 | Falta de grounding gera respostas genéricas | Médio/Alto | T3.1 a T3.5 com tenant piloto bem preparado | senior_engineer + product_ops |
| R5 | Sessão/conversa perder-se e quebrar continuidade | Alto | T1.4 como P0 | senior_engineer |
| R6 | Ações operacionais duplicadas | Alto | Idempotência mínima em T2.6 | senior_engineer |

---

## Decisões já tomadas

| Tema | Decisão |
|---|---|
| Source of truth | `theone` |
| Papel do `chatbot1` | motor conversacional/orquestrador |
| Superfície inicial | dashboard interno |
| Comunicação browser -> chatbot | proibida; passa pelo `theone` |
| Identidade do tenant | `tenant_id = client_id` |
| Expansão inicial para canais externos | não entra na release 1 |

---

## Open questions que continuam ativas

| ID | Pergunta | Owner | Estado |
|---|---|---|---|
| Q1 | Quais endpoints backend do `theone` já existem realmente? | senior_engineer | resolved for local prebooking/proxy scope |
| Q2 | Existe já modelo operacional de handoff no backend? | senior_engineer | open |
| Q3 | Onde vivem professionals e policies no backend do `theone`? | senior_engineer | open |
| Q4 | O primeiro workflow real será prebooking ou booking confirmado? | shared | resolved: prebooking |
| Q5 | O grounding inicial vai usar sync ou provider remoto? | senior_engineer | open |

---

## Checklist de readiness da release inicial

### Arquitetura
- [x] `theone` confirmado como source of truth
- [x] contrato v1 validado para a integração local atual
- [x] rotas `/api/chatbot/*` prontas

### Produto
- [ ] UI do assistente disponível no dashboard
- [x] conversa persistida
- [x] reset funcional

### Operação
- [x] prebooking real funcional
- [ ] handoff real funcional
- [x] resultado de prebooking visível/verificável dentro do CRM

### Observabilidade
- [x] `trace_id` ponta a ponta
- [x] logs básicos disponíveis
- [x] métricas mínimas instrumentadas

### Qualidade
- [x] QA local executado e fase de testes fechada
- [ ] tenant piloto validado
- [ ] blockers corrigidos

---

## Notas operacionais
- Este ficheiro deve ser mantido simples e atualizado com disciplina.
- Sempre que uma task mudar de estado, atualizar a tabela principal.
- Sempre que houver um bloqueio real, registar na coluna `Bloqueios`.
- Se o scope da release 1 mudar, atualizar também a secção de `Visão rápida`.

---

## Próximo uso recomendado
Usar este tracker como artefacto de alinhamento semanal da equipa, em conjunto com:
- `docs/chatbot1-integration-foundation.md`
- `docs/chatbot1-integration-contract.md`
- `docs/chatbot1-integration-implementation-plan.md`
