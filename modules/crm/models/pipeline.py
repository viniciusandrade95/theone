from enum import Enum


class PipelineStage(str, Enum):
    LEAD = "lead"
    BOOKED = "booked"
    COMPLETED = "completed"
