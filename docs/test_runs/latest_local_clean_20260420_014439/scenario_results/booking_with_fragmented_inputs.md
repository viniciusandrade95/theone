# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: 24f677c4-8d4f-4888-8296-57b704009270
- Session ID: s-f2730c74b01b47fe
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: Qual serviço você quer fazer no studio? Posso te ajudar com Manicure, Pedicure ou Banho de Gel.
Turn 2 user: Corte
Turn 2 assistant: Perfeito, ajustei para Corte. Não encontrei esse serviço no catálogo. Você pode escolher entre: Manicure, Pedicure, Banho de Gel?
Turn 3 user: amanhã
Turn 3 assistant: Beleza, vamos ajustar o serviço. Qual serviço você quer fazer no studio? Posso te ajudar com Manicure, Pedicure ou Banho de Gel.
Turn 4 user: 16h17
Turn 4 assistant: Beleza, vamos ajustar o serviço. Qual serviço você quer fazer no studio? Posso te ajudar com Manicure, Pedicure ou Banho de Gel.
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: Beleza, vamos ajustar o serviço. Qual serviço você quer fazer no studio? Posso te ajudar com Manicure, Pedicure ou Banho de Gel.
Turn 6 user: sim, pode confirmar
Turn 6 assistant: Qual serviço você quer fazer no studio? Posso te ajudar com Manicure, Pedicure ou Banho de Gel.
```

## Failures

- step 2: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot service to be present
- step 4: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 4: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 4: assertion_failure: expected slot service to be present
- step 5: assertion_failure: expected status awaiting_confirmation, got response=ok workflow=collecting
- step 5: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 5: assertion_failure: expected slot service to be present
- step 6: assertion_failure: expected status completed, got response=ok workflow=collecting
- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 6: assertion_failure: expected action_result.ok=True, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
