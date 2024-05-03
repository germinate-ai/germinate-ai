import typing as typ

import attr
from loguru import logger

from germinate_ai.core.exceptions import InvalidTasksDagException

from ..tasks.decorators import task_decorator_factory
from ..tasks.definition import TaskDefinition
from ..tasks.algorithms import toposort_tasks_phases, build_tasks_dag, is_dag

from .conditions import Condition, condition_decorator_factory
from .transitions import Transition


@attr.define(init=False, repr=False)
class State:
    """
    User defined State in the workflow state machine.
    """

    name: str
    _tasks: typ.Sequence["TaskDefinition"]
    _tasks_dict: dict[str, "TaskDefinition"]
    _conditions: typ.Sequence["Condition"]
    _dag: typ.Any
    _phases: typ.Sequence[typ.Sequence["TaskDefinition"]]

    def __init__(self, name: str):
        self.name = name

        self._tasks = []
        self._tasks_dict = dict()
        self._conditions = []
        self._dag = None
        self._phases = []

    # Return a task executor/task def type
    def task(self, namespace: str = "agent") -> typ.Callable:
        """Decorator that adds a task to the state's task DAG."""
        decorate = task_decorator_factory(namespace=namespace, state=self)
        return decorate

    def add_task(self, task: "TaskDefinition"):
        self._tasks.append(task)
        self._tasks_dict[task.name] = task

    def condition(self) -> typ.Callable:
        """Decorator that adds a condition to the state so that it can be used to define state transitions from it to other states."""
        decorate = condition_decorator_factory(state=self)
        return decorate

    def add_condition(self, condition: "Condition"):
        self._conditions.append(condition)

    @property
    def tasks(self) -> typ.Sequence["TaskDefinition"]:
        return self._tasks

    # TODO
    def tree(self):
        """Print tasks DAG."""
        pass

    def __and__(self, other: "Condition") -> "Transition":
        """Supports `State & Condition >> State` internal DSL by returning a new transition corresponding to `State & Condition`."""
        valid = isinstance(other, Condition)
        if not valid:
            raise TypeError("Protocol only supports `State & Condition`")
        transition = Transition(source=self, condition=other)
        return transition

    def __repr__(self) -> str:
        return f"<State: {self.name}>"

    @property
    def dag(self) -> typ.Any:
        if self._dag is None:
            self._dag = build_tasks_dag(self._tasks)
        return self._dag

    def validate(self) -> bool:
        """Validate that the tasks DAG is acyclic."""
        valid = is_dag(self.dag)
        if not valid:
            raise InvalidTasksDagException("Invalid Tasks DAG")
        

    def sorted_tasks_dag(self) -> typ.Sequence[typ.Sequence[str]]:
        """Topologically sort tasks DAG and return task names for each phase."""
        return list(toposort_tasks_phases(self.tasks))

    @property
    def conditions(self):
        return self._conditions
    
    @property
    def transitions(self):
        for condition in self._conditions:
            yield condition.transition


    def build(self):
        """Validate tasks DAG, add transition condition evaluation tasks to the DAG, figure out overall input and output schemas."""
        self.validate()

        phases = self.sorted_tasks_dag()
        # print(phases)

        # If there are multiple tasks at the end
        # add a task that merges the outputs
        if len(phases[-1]) > 1:
            raise NotImplementedError("Not implemented: more than one end task in DAG")

        # keep a ref to a task at the end of the DAG
        end_task_name = phases[-1][0]
        end_task = self._tasks_dict[end_task_name]

        # Add transition condition evaluation tasks to 
        # the DAG at the end
        for condition in self._conditions:
            transition = condition.transition
            if transition is not None and transition.is_valid():
                # print(f"Adding transition from {self} to {transition.target} on {condition}")
                # Order condition task as depending on end task
                end_task >> condition.task
                self.add_task(condition.task)
        
        phases = self.sorted_tasks_dag()
        logger.debug(f"{self.name} DAG phases: {phases}")





