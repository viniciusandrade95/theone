# theone

CRM operacional usado neste workspace como source of truth para tenants,
clientes, serviços, agenda e prebooking.

## Runbook local atual

Para operar a stack local integrada com `chatbot1`, use:

```text
/home/vinicius/system-audit/workspace/LOCAL_RUNBOOK.md
```

Resumo:
- `theone`: `/home/vinicius/system-audit/workspace/theone`
- `chatbot1`: `/home/vinicius/system-audit/workspace/chatbot1`
- `theone` local: `http://127.0.0.1:8000`
- `chatbot1` local: `http://127.0.0.1:8001`
- UI/proxy atual: `POST /api/chatbot/message` e `POST /api/chatbot/reset`
- `theone` -> `chatbot1`: `POST /message` e `POST /reset`

Comando rápido:

```bash
cd /home/vinicius/system-audit/workspace
./start_local_stack.sh
```

Parar:

```bash
cd /home/vinicius/system-audit/workspace
./stop_local_stack.sh
```

## Estado de testes local

A fase de testes do chatbot está fechada.

- Último run verde: `docs/test_runs/sidequest_local_20260422_223508`
- Signoff: `/home/vinicius/system-audit/workspace/final_test_signoff_20260422_225617/FINAL_STATUS.txt`
- Estado do projeto: `/home/vinicius/system-audit/workspace/PROJECT_STATE_REPORT.md`
- Runbook operacional: `/home/vinicius/system-audit/workspace/LOCAL_RUNBOOK.md`

Arquivos canônicos para runs sidequest:
- `hybrid_eval/summary.json`
- `autonomous/rolling_summary.json`
- `autonomous/top_failures.md`

`autonomous_tester.txt` pode ficar vazio; use os resumos JSON/Markdown como
fonte de verdade.

Este README não cobre deploy, Render ou produção.
