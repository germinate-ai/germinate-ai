import attr
import typing as typ

from pydantic import BaseModel

from .executors import TaskExecutor

if typ.TYPE_CHECKING:
    from germinate_ai.core.states import State


@attr.define(init=False, repr=False)
class TaskDefinition:
    """Represent's a user's definition of a task.

    Usually not meant to be instantiated directly.

    The `@<state>.task` decorator wraps the user defined task executor function in a `TaskDefinition` behind the scenes (actually
    wraps the functions in a `TaskExecutor` which is composed in a `TaskDefinition`.)
    """

    name: str
    state: typ.Optional["State"]

    # Define one of 
    # - executor (define your own executor), or
    # - executor_name (use a preset executor)
    executor: typ.Optional[TaskExecutor]
    executor_name: typ.Optional[str]

    _parents: set["TaskDefinition"]
    _children: set["TaskDefinition"]

    def __init__(
        self,
        name: str,
        *,
        executor: TaskExecutor = None,
        executor_name: str = None,
        state: "State" = None,
    ):
        self.name = name
        self.state = state

        self.executor = executor
        self.executor_name = executor_name

        self._parents = set()
        self._children = set()

    def __call__(self, *args: typ.Any, **kwargs: typ.Any) -> BaseModel:
        # delegate to executor
        return self.executor(*args, **kwargs)
    
    def __hash__(self):
        return hash(f"{self.state.name}.{self.name}")

    @property
    def parents(self) -> list[str]:
        return self._parents

    @property
    def children(self) -> list[str]:
        return self._children

    def add_parents(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """This task depends on other tasks."""
        if not isinstance(others, typ.Sequence):
            others = [others]

        self._parents.update(others)
        for other in others:
            other._children.add(self)

    def add_children(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """Other tasks depend on this task."""
        if not isinstance(others, typ.Sequence):
            others = [others]

        self._children.update(others)
        for other in others:
            other._parents.add(self)

    def __lshift__(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """
        Task << Task | [Task]

        This task depends on other task(s).
        """
        self.add_parents(others)
        # Note: Returning right hand side for fluent like DAG definition
        return others

    def __rshift__(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """
        Task >> Task | [Task]

        Other task(s) depend on this task.
        """
        self.add_children(others)
        # Note: Returning right hand side for fluent like DAG definition
        return others

    def __rlshift__(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """
        Task | [Task] << (this) Task

        Other task(s) depend on this task.
        """
        self.__rshift__(others)
        return self

    def __rrshift__(self, others: "TaskDefinition" | typ.Sequence["TaskDefinition"]):
        """
        Task | [Task] >> (this) task

        This task depends on other task(s).
        """
        self.__lshift__(others)
        return self

    def __repr__(self) -> str:
        state_name = ""
        if self.state:
            state_name = f"{self.state.name}."
        prefix = f"<Task: {state_name}{self.name} "
        parents = ", ".join(t.name for t in self.parents)
        children = ", ".join(t.name for t in self.children)
        return prefix + f"(parents: [{parents}], children: [{children}])>"
