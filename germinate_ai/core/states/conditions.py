from functools import wraps
import typing as typ
import asyncio

import attr
from pydantic import BaseModel

from germinate_ai.utils.di import (
    resolve_dependencies,
    # get_io_schemas_from_func,
)

from ..tasks import TaskDefinition, TaskExecutor, TaskRegistry

if typ.TYPE_CHECKING:
    from germinate_ai.core.states import State, Transition


TestConditionFunc = typ.TypeVar(
    "TestConditionFunc", bound=typ.Callable[typ.Concatenate[...], bool]
)


@attr.define(init=False, repr=False)
class Condition:
    """Conditions evaluate if a state transition should be triggered."""

    name: str

    state: "State"

    task: "TaskDefinition"
    executor: "TaskExecutor"

    transition: typ.Optional["Transition"]

    negated_condition: typ.Optional["Condition"]

    def __init__(
        self,
        name: str,
        state: "State" = None,
        transition: "Transition" = None,
        task: "TaskDefinition" = None,
        executor: "TaskExecutor" = None,
    ) -> None:
        self.name = name
        self.state = state
        self.task = task
        self.executor = executor
        self.transition = transition

    def __invert__(self) -> str:
        """Return a copy of this condition with the condition negated."""
        raise NotImplementedError("Not implemented yet.")

    def __repr__(self) -> str:
        return f"<Condition: state={self.state.name}, task={self.task.name}>"


class ConditionInputSchema(BaseModel):
    pass


class ConditionOutputSchema(BaseModel):
    condition_evaluation: bool
    """Result of evaluating the condition."""


def condition_decorator_factory(
    state: "State", namespace: str = None
) -> typ.Callable[[typ.Callable], typ.Callable]:
    """Creates a decorator that registers a state transition condition for a given State."""
    if namespace is None:
        namespace = "transition_conditions"

    def decorate(func: typ.Callable[[typ.Concatenate[...]], bool]):
        # Re-wrap the wrapped condition function in a function that matches the task executor
        # function protocol
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args: typ.Any, **kwargs: typ.Any) -> ConditionOutputSchema:
                bound = resolve_dependencies(func, *args, **kwargs)
                result = await func(*bound.args, **bound.kwargs)
                return ConditionOutputSchema(condition_evaluation=result)
        else:
            @wraps(func)
            def wrapper(*args: typ.Any, **kwargs: typ.Any) -> ConditionOutputSchema:
                bound = resolve_dependencies(func, *args, **kwargs)
                result = func(*bound.args, **bound.kwargs)
                return ConditionOutputSchema(condition_evaluation=result)

        # Compose in an executor callable
        executor_name = (
            func.__name__
            if func.__name__.endswith("executor")
            else f"{func.__name__}_executor"
        )
        executor = TaskExecutor(
            namespace=namespace,
            name=executor_name,
            # TODO
            # input schema for condition is the combined output of the final
            # phase of a state's tasks
            # output schema is always the eval schema
            # input_schema=input_schema,
            input_schema=ConditionInputSchema,
            output_schema=ConditionOutputSchema,
            callable=wrapper,
        )
        # Compose executor in a task definition so we can add it to
        # the end of a state's tasks DAG
        task = TaskDefinition(
            name=func.__name__,
            state=state,
            executor=executor,
        )
        # Compose the whole thing in a Condition
        condition = Condition(
            name=func.__name__, state=state, task=task, executor=executor
        )

        # Add condition (not the corresponding task which is added when building the DAG) to state
        state.add_condition(condition)

        # Register task executor so we can actually schedule and evaluate the condition on workers
        TaskRegistry.register(
            namespace=namespace, name=executor_name, executor=executor
        )
        return condition

    return decorate
