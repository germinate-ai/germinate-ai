import typing as typ

import attr
from loguru import logger

from germinate_ai.data.models import StateInstance, TaskInstance
from germinate_ai.data.schemas import TaskAssignment
from germinate_ai.message_bus import nats
from germinate_ai.message_bus.message_queue import NATSQueue


@attr.define(init=False)
class Scheduler:
    """Enqueue tasks ready to be assigned to workers."""

    nc: nats.NatsConnection
    connected: bool
    assignments_queue: NATSQueue

    def __init__(self, nc: nats.NatsConnection):
        self.nc = nc
        self.connected = False

    async def connect(self):
        """Connect to task assignments queue."""
        if self.connected:
            return

        self.assignments_queue = NATSQueue(
            stream="jobs",
            subject="jobs.task_assignments",
            connection=self.nc,
        )
        await self.assignments_queue.connect()
        self.connected = True

    async def enqueue_tasks(self, tasks: typ.Sequence[TaskInstance]):
        """Enqueue a sequence of tasks.
        
        Creates `TaskAssignment`s for each task and adds it to the distributed queue.
        """
        if not self.connected:
            await self.connect()

        for task in tasks:
            logger.debug(f"Queueing {task.name}")
            # create assignment and add it to the queue
            assignment = TaskAssignment(
                state_instance_id=task.state_instance_id, name=task.name
            )
            await self.assignments_queue.enqueue(assignment.model_dump_json())

    async def enqueue_state(self, state: StateInstance):
        """Enqueue the next phase (tasks that can be run in parallel) of the given state.
        
        Note: Assumes all the related task instances are accessible in `state`.
        """
        # sanity check
        if state.current_phase_index > len(state.sorted_tasks_phases) - 1:
            raise IndexError(f"State {state.name}'s current phase {state.current_phase_index} out of bounds")
        # get names of tasks in current phase
        task_names = set(state.sorted_tasks_phases[state.current_phase_index])
        # filter out corresponding tasks 
        tasks = [task for task in state.task_instances if task.name in task_names]
        # enqueue the tasks
        await self.enqueue_tasks(tasks)
