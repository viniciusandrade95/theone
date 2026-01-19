from dataclasses import dataclass
from modules.crm.models.pipeline import PipelineStage

@dataclass(frozen=True)
class CreateCustomerRequest:
    name: str
    phone: str | None = None
    email: str | None = None

@dataclass(frozen=True)
class AddInteractionRequest:
    type: str
    content: str

@dataclass(frozen=True)
class MoveStageRequest:
    to_stage: PipelineStage
