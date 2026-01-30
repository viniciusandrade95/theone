import hmac
import hashlib


def verify_signature(*, secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not secret:
        return False
    if not signature_header:
        return False
    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    supplied = signature_header.removeprefix(prefix)
    return hmac.compare_digest(expected, supplied)
