import enum


class WorkflowRunStateEnum(str, enum.Enum):
    """Workflow Run progress state."""

    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"


class StateInstanceStateEnum(str, enum.Enum):
    """State progress state."""

    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"


class TaskInstanceStateEnum(str, enum.Enum):
    """Task progress state."""

    created = "Created"
    queued = "Queued"
    in_progress = "InProgress"

    completed = "Completed"
    failed = "Failed"
    canceled = "Canceled"
