from tasks.queue import enqueue_inbound_webhook


def accept_inbound_webhook(*, payload: dict, signature_valid: bool) -> dict:
    enqueue_inbound_webhook(payload=payload, signature_valid=signature_valid)
    return {"status": "accepted"}
