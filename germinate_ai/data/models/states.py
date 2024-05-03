import typing as typ
from datetime import datetime
from typing import Any, List
from uuid import UUID
from collections import ChainMap

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from germinate_ai.core.states.conditions import ConditionOutputSchema
from germinate_ai.data.database import Base

from .enums import StateInstanceStateEnum, TaskInstanceStateEnum

if typ.TYPE_CHECKING:
    from .tasks import TaskInstance
    from .workflow_runs import WorkflowRun


class StateInstance(Base):
    """An instance of a state in a Workflow State Machine."""

    __tablename__ = "state_instances"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )

    # State name
    name: Mapped[str] = mapped_column(String())

    state: Mapped[StateInstanceStateEnum] = mapped_column(
        Enum(StateInstanceStateEnum), default=StateInstanceStateEnum.created
    )

    # Store sorted DAG generations i.e. array of (array of tasks that can be run in parallel)
    sorted_tasks_phases: Mapped[list[list[str]]] = mapped_column(JSON)
    # index of current running phase
    current_phase_index: Mapped[int] = mapped_column(default=0)

    transitions: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")

    input: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    output: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    payload: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")
    attributes: Mapped[dict[str, Any]] = mapped_column(default={}, server_default="{}")

    workflow_run_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_runs.id"))
    workflow_run: Mapped["WorkflowRun"] = relationship(
        back_populates="state_instances", foreign_keys=[workflow_run_id]
    )

    task_instances: Mapped[List["TaskInstance"]] = relationship(
        back_populates="state_instance"
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
        return f"<State Instance: {self.name}>"

    @property
    def phase_task_names(self):
        """Get the names of all the tasks in the current phase."""
        tasks = set(self.sorted_tasks_phases[self.current_phase_index])
        return tasks

    @property
    def current_phase_complete(self):
        """Are all the tasks in the current phase complete?"""
        # TODO rewrite this part
        phase_tasks = self.phase_task_names
        completed_tasks = {
            t.name
            for t in self.task_instances
            if t.state == TaskInstanceStateEnum.completed
        }
        remaining = phase_tasks.difference(completed_tasks)
        return len(remaining) == 0

    @property
    def all_phases_complete(self):
        """Are all phases in this state's tasks DAG complete?"""
        return (
            self.current_phase_complete
            and self.current_phase_index >= len(self.sorted_tasks_phases) - 1
        )

    @property
    def phase_tasks(self) -> set["TaskInstance"]:
        """Return a set of tasks in the current phase."""
        tasks= {
            t for t in self.task_instances
            if t.name in self.phase_task_names
        }
        return tasks

    def next_phase(self) -> typ.Set["TaskInstance"]:
        """Enter next phase by incrementing the phase index and returning all the tasks in the new phase.
        
        Note: Commit to persist the change.
        """
        self.current_phase_index += 1

        # sanity check
        if self.all_phases_complete:
            self.current_phase_index -= 1
            raise IndexError(f"All phases in state {self.name} already complete")

        return self.phase_tasks
    
    def final_phase(self) -> typ.Set["TaskInstance"]:
        """Return the "final" phase of tasks in the state.
        
        If a state has transitions, then the actual final phase is composed of transition condition evaluation tasks.
        In that case, this function instead returns the tasks in the penultimate phase which are actually the last phase of user defined tasks.

        Note: End states, for example, might not have any transitions into other states. 
        """
        # does this state have any transitions
        has_transitions = len(self.transitions) > 0
        if has_transitions:
            final_phase = self.sorted_tasks_phases[-2]
        else:
            final_phase = self.sorted_tasks_phases[-1]
        tasks = {
            t for t in self.task_instances
            if t.name in final_phase
        }
        return tasks
    
    def state_output(self) -> dict:
        """Returns the merged output from the final phase of tasks (see `final_phase`)."""
        outputs = dict(ChainMap(*(t.output for t in self.final_phase())))
        return outputs

    def next_state(self) -> str:
        """Figure out the next state to transition to."""
        # Get tasks corresponding to transition tas
        transition_conditions = {
            t.name: t for t in self.task_instances
            if t.name in self.transitions and t.state == TaskInstanceStateEnum.completed
        }

        # check transition condition evaluations in order
        # trigger first triggered transition
        for transition_name, target_state in self.transitions.items():
            # name -> target state
            task = transition_conditions[transition_name]
            output = ConditionOutputSchema.model_validate(task.output)
            result = output.condition_evaluation
            if result:
                return target_state

        return None