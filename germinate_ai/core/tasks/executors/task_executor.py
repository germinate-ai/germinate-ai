import inspect
import typing as typ
from collections.abc import Callable
import asyncio

import attr
from pydantic import BaseModel

from .base import BaseTaskExecutor

# TODO async type
TaskExecutorCallable = Callable[typ.Concatenate[...], BaseModel]


@attr.define(init=False, repr=False)
class TaskExecutor(BaseTaskExecutor):
    """`TaskExecutor`s execute tasks on workers.

    Task definitions, using a namespace and the executor name, specify the executor that workers should use to execute specific tasks.
    """

    namespace: str
    name: str

    input_schema: BaseModel
    output_schema: BaseModel

    callable: TaskExecutorCallable
    _callable_sig: inspect.Signature

    def __init__(
        self,
        name: str,
        callable: TaskExecutorCallable,
        *,
        input_schema: BaseModel = None,
        output_schema: BaseModel = None,
        namespace: str = "custom_tasks",
    ):
        self.namespace = namespace
        self.name = name
        self.input_schema = input_schema
        self.output_schema = output_schema

        self.callable = callable
        self._callable_sig = None

    def __call__(self, *args: typ.Any, **kwargs: typ.Any) -> BaseModel:
        return self.callable(*args, **kwargs)

    def __hash__(self):
        return hash(f"{self.namepace}.{self.name}")

    def __repr__(self) -> str:
        return f"<Task Executor: {self.name} >"
    
    def is_async(self) -> bool:
        """Is the underlying callable a coroutine function?"""
        return asyncio.iscoroutinefunction(self.callable)

    @property
    def registered_name(self) -> str:
        """Name the task executor is registered under."""
        return f"{self.namespace}.{self.name}"