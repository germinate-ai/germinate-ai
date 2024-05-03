import typing as typ

import attr

if typ.TYPE_CHECKING:
    from .states import State


@attr.define(frozen=False, init=False)
class Workflow:
    name: str
    version: str
    _states: typ.Sequence["State"]
    _initial_state: "State"

    def __init__(self, name: str, version: str = "0.1") -> None:
        self.name = name
        self.version = version
        self._states = []
        self._initial_state = None

    def add_state(self, state: "State", initial_state: bool = False):
        self._states.append(state)
        if initial_state:
            self._initial_state = state

    @property
    def workflow_id(self):
        """ID used to uniquely identify each version of this workflow."""
        return f"{self.name}:{self.version}"

    @property
    def states(self) -> typ.Sequence["State"]:
        return self._states

    @property
    def initial_state(self) -> "State":
        return self._initial_state
    
    def build(self):
        """Build workflow state machine by building tasks DAG for each state validating transitions between states."""
        for state in self._states:
            state.build()