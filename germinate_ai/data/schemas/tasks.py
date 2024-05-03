from datetime import datetime
import enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, RootModel


class TaskStateEnum(str, enum.Enum):
    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"


class TaskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    # googleai:gemini:1.5pro
    # ollama:gemma:7b
    llm: str


class TaskCreate(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    state: TaskStateEnum = TaskStateEnum.created

    job_id: Optional[UUID] = None

    executor: str

    input: dict = {}
    depends_on: list[str] = []


class TaskUpdate(BaseModel):
    state: Optional[TaskStateEnum]

    input: Optional[dict]
    output: Optional[dict]
    completed_at: Optional[datetime]


class TaskAssignment(BaseModel):
    state_instance_id: UUID
    # task_id: UUID
    name: str


class TaskSchema(TaskBase):
    state: TaskStateEnum
    job_id: UUID
    executor: str

    input: dict[str, Any]
    output: dict[str, Any] = {}


# =======================
# TODO need these??


class TaskList(RootModel):
    root: list[TaskSchema]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class TasksYAMLSpec(BaseModel):
    tasks: TaskList
