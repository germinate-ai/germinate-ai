from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.tasks import TaskInstance
from ..schemas.tasks import TaskAssignment
from ..schemas.tasks import TaskSchema as TaskSchema


def get_task_instance_from_assignment(
    db: Session, assignment: TaskAssignment
) -> TaskInstance:
    """Get Task instance from DB from the given assignment."""
    stmt = (
        select(TaskInstance)
        .where(TaskInstance.state_instance_id == assignment.state_instance_id)
        .where(TaskInstance.name == assignment.name)
    )
    task = db.scalars(stmt).first()
    return task
