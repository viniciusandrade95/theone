"""Assistant operational contracts (contract-first).

Week 1 / PR3: define stable v1 schemas for future assistant workflows.
No persistence or workflow implementation should live in this package.
"""

from modules.assistant.contracts.common import AssistantActionEnvelopeV1, AssistantActorV1, AssistantTimeWindowV1
from modules.assistant.contracts.handoff import AssistantHandoffRequestInV1, AssistantHandoffResponseOutV1
from modules.assistant.contracts.quote import AssistantQuoteRequestInV1, AssistantQuoteResponseOutV1
from modules.assistant.contracts.consult import AssistantConsultRequestInV1, AssistantConsultResponseOutV1

__all__ = [
    "AssistantActionEnvelopeV1",
    "AssistantActorV1",
    "AssistantTimeWindowV1",
    "AssistantHandoffRequestInV1",
    "AssistantHandoffResponseOutV1",
    "AssistantQuoteRequestInV1",
    "AssistantQuoteResponseOutV1",
    "AssistantConsultRequestInV1",
    "AssistantConsultResponseOutV1",
]

