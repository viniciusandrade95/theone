# booking_user_changes_time_mid_flow

- Verdict: FAIL
- Conversation ID: 21f146a6-c5e0-4530-bf5e-024c1206d77c
- Session ID: s-5428f7104c604188
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888
Turn 1 assistant: Perfeito, troquei para Corte. Resumo para confirmação: pré-agendamento de Corte no dia 21 de abr às 15:00. Tudo certo? Posso encaminhar para confirmação humana?
Turn 2 user: Na verdade muda para 16h17
Turn 2 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
Turn 3 user: sim
Turn 3 assistant: Não encontrei isso no guia deste negócio. Você quer que eu encaminhe para um atendente?
```

## Failures

- step 2: assertion_failure: expected route workflow, got rag
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: reply missing expected text: 16
- step 2: assertion_failure: expected slot service to be present
- step 2: assertion_failure: expected slot date to be present
- step 2: assertion_failure: expected slot time to be present
- step 2: assertion_failure: unexpected RAG route
- step 3: assertion_failure: expected route workflow, got rag
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: unexpected RAG route
- step 2: heuristic_failure: RAG route during operational flow
- step 3: heuristic_failure: RAG route during operational flow

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
