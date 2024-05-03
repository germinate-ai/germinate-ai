from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
# from sqlalchemy import update

from ..models.states import StateInstance


def get_state(db: Session, uuid: UUID, join_tasks=True) -> StateInstance:
    """Get State from DB."""
    stmt = select(StateInstance).where(StateInstance.id == uuid)
    if join_tasks:
        stmt = stmt.join(StateInstance.task_instances)
    return db.scalars(stmt).first()
