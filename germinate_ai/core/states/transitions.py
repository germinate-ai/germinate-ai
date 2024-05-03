import typing as typ

import attr

from .conditions import Condition

if typ.TYPE_CHECKING:
    from .states import State


@attr.define(init=False, repr=False)
class Transition:
    """Represents a transition from a source state to a target state when a condition is fulfilled."""

    _source: "State"
    _target: "State"
    _condition: Condition

    def __init__(
        self,
        source: "State" = None,
        condition: Condition = None,
        target: "State" = None,
    ) -> None:
        self._source = source
        self._condition = condition
        self._target = target
        self._condition.transition = self

    @property
    def source(self) -> "State":
        return self._source

    @property
    def target(self) -> "State":
        return self._target

    @property
    def condition(self) -> Condition:
        return self._condition

    def __rshift__(self, other: "State") -> "Transition":
        # TODO
        from .states import State
        valid = isinstance(other, State)
        if not valid:
            raise TypeError("Protocol only supports `Transition >> State`")
        self._target = other
        # TODO register transition and use it
        return self

    def is_valid(self):
        """Is a valid transaction? I.e. has valid source, target and condition."""
        return (
            self._source is not None
            and self._condition is not None
            and self._target is not None
        )

    def __repr__(self) -> str:
        return f"<Transition: {self._source.name} -> {self._target.name}>"