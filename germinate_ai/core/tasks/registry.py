
import attr

from .executors import TaskExecutor

@attr.define(frozen=True, slots=True)
class TaskKey:
    """Key used to find a task in the registry by namespace and task name."""

    namespace: str
    name: str


class TaskRegistry:
    """Registry of registered task definitions."""

    _namespaces: set[str] = set()
    _tasks: dict[TaskKey, TaskExecutor] = {}

    @classmethod
    def register(cls, namespace: str, name: str, executor: TaskExecutor):
        """Register a task executor."""
        cls._namespaces.add(namespace)
        k = TaskKey(namespace=namespace, name=name)
        # TODO check if overwrites
        cls._tasks[k] = executor

    @classmethod
    def get_executor(cls, executor_name: str) -> TaskExecutor:
        namespace, name = executor_name.split(sep=".", maxsplit=1)
        return cls.get(namespace=namespace, name=name)

    @classmethod
    def get(cls, namespace: str, name: str) -> TaskExecutor:
        """Get a registered task executor."""
        if namespace not in cls._namespaces:
            raise KeyError(f"No such namespace {namespace}")
        k = TaskKey(namespace=namespace, name=name)
        if k not in cls._tasks:
            raise KeyError(f"No task executor registered for {name}")
        return cls._tasks[k]
