from datetime import datetime
from typing import Any, List
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, String, func, text, PickleType
from sqlalchemy.orm import Mapped, mapped_column, relationship
import cloudpickle

from germinate_ai.core.tasks.executors import TaskExecutor

from ..database import Base
from .enums import TaskInstanceStateEnum
from .states import StateInstance


class TaskInstance(Base):
    """An instance of a task."""

    __tablename__ = "task_instances"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(String())

    # Just need the names to build subject and get parent tasks' outputs
    depends_on: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])

    state: Mapped[TaskInstanceStateEnum] = mapped_column(
        Enum(TaskInstanceStateEnum), default=TaskInstanceStateEnum.created
    )

    # Need either a name of a preset, or a picked executor
    task_executor_name: Mapped[str] = mapped_column(nullable=True)
    task_executor: Mapped[TaskExecutor] = mapped_column(
        PickleType(pickler=cloudpickle), nullable=True
    )

    input: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    output: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    payload: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    attributes: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")

    state_instance_id: Mapped[UUID] = mapped_column(ForeignKey("state_instances.id"))
    state_instance: Mapped["StateInstance"] = relationship(
        back_populates="task_instances"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Task Instance: {self.name}>"
