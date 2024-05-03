import typing as typ


from germinate_ai.utils.di import (
    resolve_dependencies_wrapper,
    get_io_schemas,
)

from .definition import TaskDefinition
from .executors import TaskExecutor
from .registry import TaskRegistry

if typ.TYPE_CHECKING:
    from germinate_ai.core.states import State


def task_decorator_factory(
    namespace: str, state: "State"
) -> typ.Callable[[typ.Callable], typ.Callable]:
    """Creates a decorator that registers a task execution in the given namespace."""

    def decorate(func: typ.Callable):
        # Get IO Schemas
        input_schema, output_schema = get_io_schemas(func)

        # Resolve DI arguments
        wrapper = resolve_dependencies_wrapper(func)

        # Wrap in an executor callable
        executor_name = (
            func.__name__
            if func.__name__.endswith("executor")
            else f"{func.__name__}_executor"
        )
        executor = TaskExecutor(
            namespace=namespace,
            name=executor_name,
            input_schema=input_schema,
            output_schema=output_schema,
            callable=wrapper,
        )

        # Wrap executor in a task definition
        task = TaskDefinition(
            name=func.__name__,
            state=state,
            executor=executor,
        )

        # Add to state
        state.add_task(task)
        
        # Register task executor
        TaskRegistry.register(
            namespace=namespace, name=executor_name, executor=executor
        )
        return task

    return decorate
