from abc import abstractmethod
from collections.abc import Callable
import typing as typ


class BaseTaskExecutor(Callable[typ.Concatenate[...], typ.Any]):
    """Base class for task executors."""

    # The name used to find this executor from the registry
    name: str

    @abstractmethod
    def __call__(self, *args: typ.Any, **kwargs: typ.Any) -> typ.Any:
        pass


