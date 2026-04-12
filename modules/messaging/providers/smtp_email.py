from __future__ import annotations

import smtplib
import ssl
import uuid
from dataclasses import dataclass
from email.message import EmailMessage

from modules.messaging.providers.outbound_provider import OutboundSendResult


@dataclass(frozen=True)
class SmtpEmailConfig:
    host: str
    port: int
    username: str | None
    password: str | None
    from_email: str
    timeout_seconds: int
    use_starttls: bool


class SmtpEmailProvider:
    def __init__(self, config: SmtpEmailConfig):
        self.config = config

    @staticmethod
    def from_config(app_config) -> "SmtpEmailProvider | None":
        host = getattr(app_config, "SMTP_HOST", None)
        from_email = getattr(app_config, "SMTP_FROM", None)
        if not host or not from_email:
            return None
        port = int(getattr(app_config, "SMTP_PORT", 587) or 587)
        username = getattr(app_config, "SMTP_USERNAME", None)
        password = getattr(app_config, "SMTP_PASSWORD", None)
        timeout_seconds = int(getattr(app_config, "SMTP_TIMEOUT_SECONDS", 10) or 10)
        use_starttls = bool(getattr(app_config, "SMTP_USE_STARTTLS", True))
        return SmtpEmailProvider(
            SmtpEmailConfig(
                host=str(host),
                port=port,
                username=str(username) if username else None,
                password=str(password) if password else None,
                from_email=str(from_email),
                timeout_seconds=timeout_seconds,
                use_starttls=use_starttls,
            )
        )

    def send_email_text(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
        trace_id: str,
        idempotency_key: str | None = None,
    ) -> OutboundSendResult:
        msg = EmailMessage()
        msg["From"] = self.config.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["X-Trace-Id"] = trace_id
        if idempotency_key:
            msg["Idempotency-Key"] = idempotency_key
        msg.set_content(body or "")

        context = ssl.create_default_context()
        with smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout_seconds) as smtp:
            smtp.ehlo()
            if self.config.use_starttls:
                smtp.starttls(context=context)
                smtp.ehlo()
            if self.config.username and self.config.password:
                smtp.login(self.config.username, self.config.password)
            smtp.send_message(msg)

        # SMTP does not provide a provider message id; generate a stable id for traceability.
        return OutboundSendResult(provider="smtp", provider_message_id=str(uuid.uuid4()))

