# Checklist de Teste Ponta a Ponta — Piloto `theone` + `chatbot1`

## Objetivo
Este checklist serve para validar o primeiro fluxo real da integração entre `theone` e `chatbot1`.

### Workflow alvo
- `book_appointment` como **prebooking / booking assistido**

### Endpoint fonte de execução
- `POST /crm/assistant/prebook`

### Objetivo do piloto
Confirmar que a conversa no assistente consegue gerar um efeito real e verificável no CRM, com rastreabilidade, sem duplicação e com tratamento correto de conflitos e erros.

---

## Pré-requisitos do ambiente

### Infra e configuração
- [ ] `theone` a correr com as alterações da integração aplicadas
- [ ] `chatbot1` a correr com `TheOneConnector` ativo
- [ ] `THEONE_BASE_URL` configurado no `chatbot1`
- [ ] `THEONE_ENABLED=true` no `chatbot1`
- [ ] `ASSISTANT_CONNECTOR_TOKEN` configurado no `theone`
- [ ] token/header interno do connector alinhado entre os dois serviços
- [ ] `CHATBOT_SERVICE_BASE_URL` configurado no `theone`
- [ ] tracing/logs acessíveis em ambos os serviços

### Tenant piloto
- [ ] 1 tenant piloto criado
- [ ] `tenant_id` confirmado
- [ ] 1 location válida criada
- [ ] timezone correta configurada
- [ ] 2 a 3 services válidos criados
- [ ] booking settings configurados
- [ ] dashboard assistant acessível para esse tenant

### Dados de teste
- [ ] 1 customer existente com telefone/email válidos
- [ ] possibilidade de testar customer novo
- [ ] pelo menos 1 slot livre para teste
- [ ] pelo menos 1 slot já ocupado para teste de conflito

---

## Cenário 1 — Smoke test de conectividade

### Objetivo
Garantir que a conversa chega ao `chatbot1` e volta ao `theone` corretamente.

### Passos
- [ ] abrir o assistant no dashboard do `theone`
- [ ] enviar uma mensagem simples, por exemplo: "Olá"
- [ ] receber resposta do assistant
- [ ] validar que não houve chamada direta do browser ao `chatbot1`
- [ ] validar que existe `trace_id` na interação

### Resultado esperado
- [ ] resposta recebida no UI
- [ ] logs do `theone` e `chatbot1` correlacionáveis por `trace_id`
- [ ] nenhuma credencial de serviço exposta ao browser

---

## Cenário 2 — Fluxo feliz de prebooking

### Objetivo
Validar que o assistant conduz o booking e cria um registo real no `theone`.

### Exemplo de prompt inicial
"Quero marcar uma limpeza de pele amanhã às 15h"

### Passos
- [ ] abrir o assistant no dashboard
- [ ] iniciar pedido de marcação
- [ ] deixar o assistant recolher qualquer slot em falta
- [ ] confirmar explicitamente a marcação
- [ ] validar que o `chatbot1` executa `POST /crm/assistant/prebook`
- [ ] validar que o `theone` responde com sucesso
- [ ] validar que foi criado um registo visível no CRM
- [ ] validar que o registo foi criado com `needs_confirmation=true`

### Resultado esperado
- [ ] o utilizador recebe mensagem de confirmação coerente
- [ ] o CRM contém o registo correspondente
- [ ] `trace_id` está presente ponta a ponta
- [ ] `idempotency_key` foi enviada

---

## Cenário 3 — Customer existente

### Objetivo
Validar resolução correta de customer já existente.

### Passos
- [ ] usar dados de um customer já existente
- [ ] repetir o fluxo de marcação
- [ ] validar se o `theone` associa corretamente ao customer existente

### Resultado esperado
- [ ] não cria customer duplicado sem necessidade
- [ ] o registo criado aponta para o customer correto

---

## Cenário 4 — Customer novo

### Objetivo
Validar criação ou tratamento correto de customer inexistente.

### Passos
- [ ] iniciar booking com nome/telefone/email ainda não existentes
- [ ] confirmar marcação
- [ ] validar comportamento do `theone`

### Resultado esperado
- [ ] customer novo é criado ou resolvido corretamente conforme a regra implementada
- [ ] prebooking é criado com associação coerente

---

## Cenário 5 — Conflito de agenda

### Objetivo
Validar conflito real e resposta elegante do assistant.

### Passos
- [ ] escolher um slot que já esteja ocupado
- [ ] executar o fluxo completo até à confirmação
- [ ] validar que o `theone` responde com `409 APPOINTMENT_OVERLAP`
- [ ] validar que o `chatbot1` transforma isso numa resposta utilizável

### Resultado esperado
- [ ] não cria registo duplicado/inválido
- [ ] utilizador recebe mensagem clara
- [ ] erro fica rastreável por `trace_id`

---

## Cenário 6 — Idempotência / retry

### Objetivo
Garantir que confirmações repetidas não criam duplicados.

### Passos
- [ ] executar um booking com sucesso
- [ ] repetir a confirmação rapidamente
- [ ] simular retry da mesma operação, se possível
- [ ] validar a persistência de idempotência do `theone`

### Resultado esperado
- [ ] não cria múltiplos registos para a mesma confirmação
- [ ] a resposta é estável e previsível

---

## Cenário 7 — Data e timezone

### Objetivo
Validar que a interpretação de data/hora está correta.

### Passos
- [ ] marcar um serviço usando linguagem natural
- [ ] confirmar a data/hora apresentada pelo assistant
- [ ] comparar com `starts_at` / `ends_at` persistidos no `theone`
- [ ] validar timezone do tenant/location

### Resultado esperado
- [ ] hora mostrada ao utilizador corresponde ao que é persistido
- [ ] duração do serviço é respeitada
- [ ] não há offset indevido por UTC/timezone

### Atenção especial
- `starts_at` / `ends_at` foram descritos como best-effort UTC derivations no `chatbot1`
- este é um dos pontos mais sensíveis do piloto

---

## Cenário 8 — Persistência da conversa

### Objetivo
Validar continuidade mínima da conversa no `theone`.

### Passos
- [ ] iniciar conversa
- [ ] enviar algumas mensagens
- [ ] recarregar a página
- [ ] validar se a conversa/sessão continua coerente

### Resultado esperado
- [ ] `conversation_id` persiste
- [ ] `chatbot_session_id` continua alinhado
- [ ] não perde completamente o contexto de produto

---

## Cenário 9 — Reset de conversa

### Objetivo
Validar reset funcional sem quebrar o sistema.

### Passos
- [ ] iniciar conversa
- [ ] usar reset
- [ ] iniciar nova conversa

### Resultado esperado
- [ ] nova sessão gerada quando necessário
- [ ] conversa anterior não interfere na nova

---

## Cenário 10 — Erro interno controlado

### Objetivo
Garantir comportamento aceitável quando algo falha no backend.

### Passos
- [ ] simular ou provocar falha controlada no caminho operacional
- [ ] observar resposta do assistant
- [ ] validar logs no `theone` e no `chatbot1`

### Resultado esperado
- [ ] utilizador não recebe erro cru/obscuro
- [ ] logs têm informação suficiente para diagnóstico
- [ ] `trace_id` permite correlação

---

## Verificações obrigatórias pós-teste

### No `theone`
- [ ] registo criado aparece no CRM
- [ ] `needs_confirmation=true` quando esperado
- [ ] tenant correto
- [ ] customer correto
- [ ] service correto
- [ ] horário correto

### No `chatbot1`
- [ ] workflow executado foi `book_appointment`
- [ ] `TheOneConnector` foi realmente usado
- [ ] `trace_id` propagado
- [ ] `idempotency_key` enviada
- [ ] conflito/erro parseado corretamente

### Na experiência do utilizador
- [ ] mensagem final clara
- [ ] sem resposta enganosa
- [ ] sem prometer booking confirmado quando é só prebooking

---

## Critérios de sucesso do piloto

O piloto pode ser considerado bem-sucedido quando:
- [ ] o fluxo feliz funciona ponta a ponta
- [ ] conflito de agenda é tratado corretamente
- [ ] idempotência evita duplicados
- [ ] timezone/datas estão corretos
- [ ] customer existing/new funciona de forma coerente
- [ ] `trace_id` funciona ponta a ponta
- [ ] o registo criado é verificável no CRM

---

## Critérios para NÃO avançar de fase

Não expandir para novos workflows/canais se algum destes falhar:
- [ ] booking cria duplicados
- [ ] conflito não é tratado corretamente
- [ ] timezone está incorreto
- [ ] customer resolution é inconsistente
- [ ] o CRM não reflete corretamente o resultado
- [ ] tracing/logs não permitem diagnosticar erros

---

## Bugs / observações encontradas

| ID | Severidade | Cenário | Descrição | Serviço | Estado |
|---|---|---|---|---|---|
| BUG-001 |  |  |  |  |  |
| BUG-002 |  |  |  |  |  |
| BUG-003 |  |  |  |  |  |

---

## Decisão final do piloto

### Resultado geral
- [ ] aprovado para continuar
- [ ] aprovado com restrições
- [ ] não aprovado

### Próximo passo decidido
- [ ] corrigir blockers
- [ ] repetir piloto
- [ ] avançar para grounding melhorado
- [ ] avançar para handoff/quote/consult
- [ ] avaliar expansão para outros canais
