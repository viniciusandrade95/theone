# Local Dev Runbook

Este runbook aponta para o fluxo local atual do workspace. Ele é local-only e
não deve ser usado para deploy, Render ou produção.

## Fonte operacional

Use o runbook consolidado:

```text
/home/vinicius/system-audit/workspace/LOCAL_RUNBOOK.md
```

## Stack local

- Workspace: `/home/vinicius/system-audit/workspace`
- `theone`: `/home/vinicius/system-audit/workspace/theone`
- `chatbot1`: `/home/vinicius/system-audit/workspace/chatbot1`
- `theone` API: `http://127.0.0.1:8000`
- `chatbot1` API: `http://127.0.0.1:8001`

## Comandos

Subir stack:

```bash
cd /home/vinicius/system-audit/workspace
./start_local_stack.sh
```

Subir serviços separadamente:

```bash
cd /home/vinicius/system-audit/workspace
./start_theone.sh
./capture_runtime_auth.sh
./start_chatbot1.sh
```

Capturar auth runtime novamente:

```bash
cd /home/vinicius/system-audit/workspace
./capture_runtime_auth.sh
source ./runtime_auth.env
```

Evidência rápida:

```bash
cd /home/vinicius/system-audit/workspace
./quick_chatbot_evidence.sh
```

Sidequest local, apenas se uma nova rodada for explicitamente necessária:

```bash
cd /home/vinicius/system-audit/workspace
./run_sidequest_loop.sh
```

Comparar runs:

```bash
cd /home/vinicius/system-audit/workspace
./compare_sidequest_runs.py sidequest_local_OLD sidequest_local_NEW
```

Parar stack:

```bash
cd /home/vinicius/system-audit/workspace
./stop_local_stack.sh
```

## Estado verde atual

- Último run verde: `docs/test_runs/sidequest_local_20260422_223508`
- Signoff: `/home/vinicius/system-audit/workspace/final_test_signoff_20260422_225617/FINAL_STATUS.txt`
- Relatório: `/home/vinicius/system-audit/workspace/PROJECT_STATE_REPORT.md`

Resultados do signoff:
- `hybrid_eval`: 14 pass / 0 fail / 0 partial
- `autonomous`: 95 pass / 0 fail / 0 partial
- top failures: none
- compare: 59 -> 0 failure signals

Arquivos canônicos:
- `hybrid_eval/summary.json`
- `autonomous/rolling_summary.json`
- `autonomous/top_failures.md`

`autonomous_tester.txt` pode ficar vazio; não use esse arquivo como fonte de
verdade.

## Próximo foco

- consolidação do ritual local
- robustez curta sem refactor amplo
- piloto interno controlado
- não reabrir sidequest debugging por defeito
