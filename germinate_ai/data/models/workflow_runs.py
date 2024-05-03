from datetime import datetime
from typing import TYPE_CHECKING, Any, List
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, text, PickleType
from sqlalchemy.orm import Mapped, mapped_column, relationship
import cloudpickle

from germinate_ai.core.workflows import Workflow

from ..database import Base

from .enums import WorkflowRunStateEnum

if TYPE_CHECKING:
    from .states import StateInstance


class WorkflowRun(Base):
    """One particular run of a workflow."""
    __tablename__ = "workflow_runs"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    """Workflow run UUID"""

    workflow_name: Mapped[str] = mapped_column(String())
    
    workflow_version: Mapped[str] = mapped_column(String())
    
    workflow_id: Mapped[str] = mapped_column(String())


    # picked workflow state_machine
    workflow_state_machine: Mapped[Workflow] = mapped_column(
        PickleType(pickler=cloudpickle), nullable=True
    )

    state: Mapped[WorkflowRunStateEnum] = mapped_column(
        Enum(WorkflowRunStateEnum), default=WorkflowRunStateEnum.created
    )

    input: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    output: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    payload: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    attributes: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")

    state_instances: Mapped[List["StateInstance"]] = relationship(
        back_populates="workflow_run", foreign_keys="StateInstance.workflow_run_id"
    )

    # Track name of initial state
    initial_state_name: Mapped[str] = mapped_column(String())

    current_state_id: Mapped[UUID] = mapped_column(
        ForeignKey("state_instances.id"), nullable=True
    )
    current_state: Mapped["StateInstance"] = relationship(
        foreign_keys=[current_state_id], post_update=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Workflow Run: {self.name}>"


    def state_instance_by_name(self, name: str) -> "StateInstance":
        """Find related state instance by name."""
        try:
            return next(si for si in self.state_instances if si.name == name)
        except StopIteration:
            return None