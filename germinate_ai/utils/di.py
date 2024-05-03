import asyncio
from collections.abc import Callable
import typing as typ
from functools import wraps
import inspect

from pydantic import BaseModel


# TODO key deps by name, args, type etc instead of just callable name
class Depends:
    """Simple Dependency injection implementation similar to FastAPI."""

    _cache: dict[Callable, typ.Any] = {}

    def __init__(self, dependency: Callable, *args: typ.Any, **kwargs: typ.Any):
        self.dependency = dependency
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> typ.Any:
        if self.dependency in Depends._cache:
            return Depends._cache[self.dependency]

        result = self.dependency(*self.args, **self.kwargs)
        Depends._cache[self.dependency] = result
        return result


def get_io_schemas(func: typ.Callable) -> tuple[BaseModel, BaseModel]:
    """Get input and output schemas (Pydantic models) from the function signature."""
    # Get input and output schemas from signature/type hints
    signature = inspect.signature(func)
    type_hints = typ.get_type_hints(func)

    # might not take any input/output
    input_schema = BaseModel
    output_schema = BaseModel

    if "input" in type_hints:
        input_type = type_hints["input"]
        if issubclass(input_type, BaseModel):
            input_schema = input_type

    if signature.return_annotation == signature.empty:
        # TODO appropriate error type
        raise TypeError(f"Task {func.__name__} does not specify an output schema")
    if "return" in type_hints:
        output_type = type_hints["return"]
        if issubclass(output_type, BaseModel):
            output_schema = output_type

    return input_schema, output_schema


def resolve_dependencies(func: typ.Callable, *args: typ.Any, **kwargs: typ.Any) -> inspect.BoundArguments:
    """Returns bound arguments with dependencies resolved."""
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    for k, arg in bound.arguments.items():
        if type(arg) == Depends:
            bound.arguments[k] = arg()

    return bound



def resolve_dependencies_wrapper(func: typ.Callable):
    """Returns a function wrapper that binds func arguments, applies defaults and resolves any dependency injections."""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            bound = resolve_dependencies(func, *args, **kwargs)
            return await func(*bound.args, **bound.kwargs)
        return wrapper

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = resolve_dependencies(func, *args, **kwargs)
        return func(*bound.args, **bound.kwargs)
    return wrapper
