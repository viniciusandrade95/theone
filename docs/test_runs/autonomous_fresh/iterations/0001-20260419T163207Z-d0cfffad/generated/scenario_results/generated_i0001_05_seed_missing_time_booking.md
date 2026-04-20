# generated_i0001_05_seed_missing_time_booking

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-6b1f7737c745473d
- Judge: DISABLED

## Transcript

```text
Turn 1 user: quero marcar mas nao sei horario
Turn 1 assistant: Qual serviço você deseja? Posso ajudar com o corte.
Turn 2 user: corte amanhã
Turn 2 assistant: Perfeito, já ajustei para Corte. Qual horário fica melhor para você?
Turn 3 user: de tarde
Turn 3 assistant: Desculpe, a integração está temporariamente indisponível. Vou encaminhar para atendimento humano.
Turn 4 user: Audit User, telefone 11999998888
Turn 4 assistant: Tudo certo, já fiz o ajuste. Qual horário funciona melhor pra você?
Turn 5 user: ok
Turn 5 assistant: Qual horário funciona melhor para você?
```

## Failures

- step 1: assertion_failure: workflow appears to have reset to collecting with empty slots
- step 5: heuristic_failure: Repeated time question
- heuristic_failure: Expected final status awaiting_confirmation, got collecting

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
