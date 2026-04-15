import hmac
import hashlib


def verify_signature(*, secret: str, payload: bytes, signature_header: str | None) -> bool:
    secret = (secret or "").strip()
    if not secret:
        return False
    if not signature_header:
        return False
    signature_header = signature_header.strip()
    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    supplied = signature_header.removeprefix(prefix).strip().lower()
    return hmac.compare_digest(expected, supplied)
