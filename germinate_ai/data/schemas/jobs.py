from typing import Optional, Any
from uuid import UUID
import enum

from pydantic import BaseModel, ConfigDict


class JobStateEnum(str, enum.Enum):
    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"


class JobBase(BaseModel):
    name: str


class JobCreate(JobBase):
    model_config = ConfigDict(from_attributes=True)

    state: JobStateEnum = JobStateEnum.created

    workflow_run_id: Optional[UUID] = None

    sorted_tasks_phases: list[list[str]]
    current_phase_index: int = 0


class JobUpdate(BaseModel):
    state: Optional[JobStateEnum]

    topological_sorted_steps: Optional[dict[str, Any]]
    sorted_task_generations: Optional[dict[str, Any]]
    current_generation_index: Optional[dict[str, Any]]


class Job(JobBase):
    model_config = ConfigDict(from_attributes=True)

    state: JobStateEnum
