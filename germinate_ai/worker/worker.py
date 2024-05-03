"""
This module implements a Worker class that waits for task assignments from the message bus, hands over assignments to the TaskDispatcher, and notifies
listeners on task completions via the message bus.
"""

import asyncio
import time

from loguru import logger
from pydantic import ValidationError

from germinate_ai.data.schemas.tasks import TaskAssignment
from germinate_ai.message_bus import nats
from germinate_ai.message_bus.message_queue import NATSQueue

# from germinate_ai.tasks.executors.agent_task_executor import AgentTaskExecutor, pm_agent_strategy
from germinate_ai.utils.helpers import get_next_tick

from .task_dispatcher import TaskDispatcher


class Worker:
    """Polls and processes tasks from the assignments queue."""

    def __init__(
        self,
        nc: nats.NatsConnection,
        task_dispatcher: TaskDispatcher,
        id: int = 0,
        tick_interval: int = 10,
    ):
        self.nc = nc
        self.id = id
        self.tick_interval = tick_interval
        self.task_dispatcher = task_dispatcher

    async def run(self):
        """Connect to messaging bus, wait for assignments, and execute them."""
        next_tick = get_next_tick(self.tick_interval)

        await self.connect()
        logger.success(f"Worker #{self.id}: connected to cluster! Waiting for tasks...")

        while True:
            last_tick = time.time()

            try:
                msg = await self.assignments_queue.dequeue()
                task_json = msg.data
                # acknowledge message so we don't see it again
                await msg.ack()
                success = await self._run_task(task_json)
                if not success:
                    logger.exception("Task execution failure", task_json)
            except TimeoutError:
                pass
            except asyncio.CancelledError:
                logger.debug(f"Worker #{self.id}: Cancelled! Shutting down worker...")
                break
            except Exception as e:
                logger.exception("Error while reading from NATS queue: ", e)

            await asyncio.sleep(next_tick(last_tick=last_tick))

    async def connect(self):
        """Connect to task assignments and completions queue so we can get assignments/send task completion notifications via the message bus."""
        self.assignments_queue = NATSQueue(
            stream="jobs",
            subject="jobs.task_assignments",
            durable_consumer="task_runner",
            connection=self.nc,
        )
        await self.assignments_queue.connect()
        # TODO write only:
        self.completions_queue = NATSQueue(
            connection=self.nc, stream="jobs", subject="jobs.task_completions"
        )
        await self.completions_queue.connect()

    async def _run_task(self, task_json: str) -> bool:
        """Validate task assignment data, delegate execution to TaskDispatcher, and notify listeners on completion via the messaging bus."""
        try:
            assignment = TaskAssignment.model_validate_json(task_json)
        except ValidationError as e:
            logger.error(f"Worker #{self.id}: Skipping invalid task `{task_json}`: {e}")
            return

        logger.info(f"Worker #{self.id}: Starting task {assignment.name}")
        task = await self.task_dispatcher.execute(assignment=assignment)

        # Queue task completed message
        logger.debug(f"Queueing completed message {task.name}")
        await self.completions_queue.enqueue(assignment.model_dump_json())

        # return True => mark task as completed
        # TODO handle failures
        return True
