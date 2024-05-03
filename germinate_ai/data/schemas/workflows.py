from collections import deque
from typing import Sequence

from pydantic import BaseModel, RootModel


class TaskDefinition(BaseModel):
    name: str
    executor: str
    depends_on: list[str] = []
    llm: str

    stage: str | None = None

    input: dict = {}
    output: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Attach to current stage. if any
        current_stage = StageContext.get_current_stage()
        if current_stage is None:
            return

        self.stage = current_stage.name
        current_stage.tasks.append(self)

    def set_sinks(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """Other tasks depend on this task."""
        if not isinstance(others, Sequence):
            others = [others]

        for other in others:
            other.depends_on.append(self.name)

    def set_sources(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """This task depends on other tasks."""
        if not isinstance(others, Sequence):
            others = [others]

        for other in others:
            self.depends_on.append(other.name)

    def __lshift__(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """
        Task << Task | [Task]

        This task depends on other task(s).
        """
        self.set_sources(others)
        # Note: Returning right hand side for fluent like DAG definition
        return others

    def __rshift__(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """
        Task >> Task | [Task]

        Other task(s) depend on this task.
        """
        self.set_sinks(others)
        # Note: Returning right hand side for fluent like DAG definition
        return others

    def __rlshift__(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """
        Task | [Task] << (this) Task

        Other task(s) depend on this task.
        """
        self.__rshift__(others)
        return self

    def __rrshift__(self, others: "TaskDefinition" | Sequence["TaskDefinition"]):
        """
        Task | [Task] >> (this) task

        This task depends on other task(s).
        """
        self.__lshift__(others)
        return self


class TaskDefinitions(RootModel):
    root: list[TaskDefinition]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def append(self, item):
        self.root.append(item)


class Stage(BaseModel):
    name: str
    tasks: TaskDefinitions = TaskDefinitions([])

    def __enter__(self):
        StageContext.push(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        StageContext.pop()


class StageContext:
    _stages: deque[Stage] = deque()

    @classmethod
    def push(cls, stage: Stage):
        cls._stages.append(stage)

    @classmethod
    def pop(cls) -> Stage | None:
        stage = cls._stages.pop()
        return stage

    @classmethod
    def get_current_stage(cls) -> Stage | None:
        try:
            # try to peek at last item
            return cls._stages[-1]
        except IndexError:
            return None


class Stages(RootModel):
    root: list[Stage]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def append(self, item):
        self.root.append(item)


class Workflow(BaseModel):
    name: str
    stages: Stages = Stages([])

    def add_stage(self, name: str):
        stage = Stage(name=name)
        self.stages.append(stage)
        return stage

    def __hash__(self) -> int:
        # TODO hash by all stages -> tasks etc recursively (s/t can track if changed)
        return hash(self.name)


class WorkflowYAMLSpec(BaseModel):
    workflow: Workflow
