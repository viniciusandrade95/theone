from dataclasses import dataclass

@dataclass(frozen=True)
class MessageReceived:
    tenant_id: str
    payload: dict
