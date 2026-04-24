# generated_i0002_05_seed_colloquial_fragmented_booking

- Verdict: FAIL
- Conversation ID: b0c58bb7-29ce-4b4a-9f83-7fa7715f7e35
- Session ID: s-9e91b34816284b18
- Judge: DISABLED

## Transcript

```text
Turn 1 user: mano queria cortar amanhã
Turn 1 assistant: Não consigo iniciar esse fluxo com segurança porque a configuração deste negócio está incompleta. Vou encaminhar para um atendente continuar sem inventar dados.
Turn 2 user: pode ser corte
Turn 2 assistant: Posso ajudar com seu corte. Quer saber o preço, ver detalhes ou já marcar?
Turn 3 user: 16h? nao, 17h melhor
Turn 3 assistant: Tudo certo, mudei para Corte. Qual dia funciona melhor para você?
Turn 4 user: Audit User, 11999998888
Turn 4 assistant: 
Turn 5 user: sim
Turn 5 assistant: Qual dia fica melhor para você?
```

## Failures

- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: unexpected RAG route
- step 4: upstream_runtime_failure: HTTP request failed with status 502: <html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>cloudflare</center>
</body>
</html>

- step 4: upstream_runtime_failure: response body is not a JSON object
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 2: heuristic_failure: RAG route during operational flow
- step 3: heuristic_failure: Slot loss detected: date
- step 5: heuristic_failure: Slot loss detected: date
- heuristic_failure: Expected final status completed, got collecting

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
