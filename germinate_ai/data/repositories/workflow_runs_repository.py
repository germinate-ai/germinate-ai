from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from germinate_ai.core.workflows import Workflow

from ..models.enums import WorkflowRunStateEnum
from ..models.workflow_runs import WorkflowRun


def get_workflow_run(db: Session, uuid: UUID, join_states=True) -> WorkflowRun:
    """Get WorkflowRun from the DB."""
    stmt = select(WorkflowRun).where(WorkflowRun.id == uuid)
    if join_states:
        stmt = stmt.join(WorkflowRun.state_instances)
    return db.scalars(stmt).first()


def create_run_from_workflow(db: Session, workflow: Workflow) -> WorkflowRun:
    """Create a WorkflowRun model from a Workflow specification."""
    workflow_run = WorkflowRun(
        workflow_name=workflow.name,
        workflow_version=workflow.version,
        workflow_id=workflow.workflow_id,
    )
    workflow_run.state = WorkflowRunStateEnum.created
    return workflow_run
