import enum

from pydantic import BaseModel, ConfigDict


class WorkflowRunStateEnum(str, enum.Enum):
    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"


class WorkflowRunBase(BaseModel):
    workflow_name: str


class WorkflowRunCreate(WorkflowRunBase):
    model_config = ConfigDict(from_attributes=True)

    state: WorkflowRunStateEnum = WorkflowRunStateEnum.created


class WorkflowRunUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: WorkflowRunStateEnum
