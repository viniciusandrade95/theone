import base64
import hmac
import hashlib
import json
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthToken:
    tenant_id: str
    user_id: str
    exp: int


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def issue_token(*, secret: str, tenant_id: str, user_id: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url(payload_bytes)

    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64url(sig)

    return f"{payload_b64}.{sig_b64}"


def verify_token(*, secret: str, token: str) -> AuthToken:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        raise RuntimeError("invalid_token_format")

    expected_sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url(expected_sig), sig_b64):
        raise RuntimeError("invalid_token_signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))

    exp = int(payload["exp"])
    if int(time.time()) > exp:
        raise RuntimeError("token_expired")

    return AuthToken(
        tenant_id=str(payload["tenant_id"]),
        user_id=str(payload["user_id"]),
        exp=exp,
    )
