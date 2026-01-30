from celery import Celery, Task

from core.config import get_config, load_config
from app.container import build_container
from tasks.workers.messaging.inbound_worker import process_inbound_webhook


_celery_app: Celery | None = None
_inbound_task = None


def create_celery_app() -> Celery:
    load_config()
    cfg = get_config()
    app = Celery("theone", broker=cfg.REDIS_URL, backend=cfg.REDIS_URL)
    app.conf.task_always_eager = cfg.CELERY_TASK_ALWAYS_EAGER or cfg.ENV == "test"
    app.conf.task_acks_late = True
    app.conf.task_reject_on_worker_lost = True
    return app


def get_celery_app() -> Celery:
    global _celery_app, _inbound_task
    if _celery_app is None:
        _celery_app = create_celery_app()
        _inbound_task = _celery_app.task(
            bind=True,
            base=InboundWebhookTask,
            autoretry_for=(Exception,),
            retry_backoff=True,
            retry_kwargs={"max_retries": 5},
        )(_inbound_webhook_task)
    return _celery_app


class InboundWebhookTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        payload = None
        if args:
            payload = args[0]
        if isinstance(payload, dict):
            container = build_container()
            provider = payload.get("provider", "").strip().lower()
            phone_number_id = payload.get("phone_number_id", "").strip()
            account = container.messaging_repo.get_whatsapp_account(
                provider=provider,
                phone_number_id=phone_number_id,
            )
            if account is not None:
                container.messaging_repo.mark_webhook_event_status(
                    tenant_id=account.tenant_id,
                    provider=provider,
                    external_event_id=payload.get("external_event_id", ""),
                    status="dead_letter",
                )


def _inbound_webhook_task(self, payload: dict, signature_valid: bool) -> dict:
    container = build_container()
    return process_inbound_webhook(
        inbound_service=container.inbound_webhook_service,
        payload=payload,
        signature_valid=signature_valid,
    )


def enqueue_inbound_webhook(*, payload: dict, signature_valid: bool):
    get_celery_app()
    return _inbound_task.apply_async(args=[payload, signature_valid])
