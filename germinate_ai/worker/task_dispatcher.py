import typing as typ
from collections import ChainMap

from loguru import logger

from germinate_ai.data.models import TaskInstance
from germinate_ai.data.schemas.messages import Message
from germinate_ai.data.schemas.tasks import TaskAssignment, TaskStateEnum
from germinate_ai.data.repositories.tasks_repository import get_task_instance_from_assignment
from germinate_ai.message_bus import nats
from germinate_ai.message_bus.message_queue import NATSQueue
from germinate_ai.core.tasks.registry import TaskRegistry


class TaskDispatcher:
    """
    Dispatches tasks to appropriate executors, and updates task state accordingly.

    Given an enqueued task data, TaskDispatcher gets the correct executor from TaskRegistry and uses it to run the corresponding Task.

    TaskDispatcher also validates input and output schemas for the task, and updates the task's state before ("queued"),
    and after ("completed"/"failed") execution.
    """

    def __init__(self, nc: nats.NatsConnection, sessionmaker: typ.Callable):
        self.nc = nc
        self.sessionmaker = sessionmaker

    async def execute(self, assignment: TaskAssignment) -> TaskInstance:
        """Execute the enqueued task.
        
        Args:
            assignment (TaskAssignment): Task assignment data

        Returns:
            TaskInstance: SQLAlchemy model representing persisted task state
        """
        with self.sessionmaker() as db:
            # Get corresponding task from DB
            task = get_task_instance_from_assignment(db, assignment)
            if task is None:
                logger.error(f"No such task: skipping `{assignment}`")
                return None

            # Get executor for the task
            executor = TaskRegistry.get_executor(task.task_executor_name)

            # Get task inputs from dependencies' outputs
            task_input = await self._get_task_inputs(task)

            # Validate task input
            task_input = executor.input_schema.model_validate(task_input)

            # Update task's input
            task.input = task_input.model_dump()

            # Update task's state
            task.state = TaskStateEnum.queued
            db.add(task)
            db.commit()

            # TODO Run task executor pre-exec hook, if any

            # Run the task with executor
            # TODO handle failures
            # TODO async tasks
            logger.debug(
                f"Executing task {task.name} with executor {task.task_executor_name}..."
            )
            if executor.is_async():
                output = await executor(task_input)
            else:
                output = executor(task_input)

            # Validate task output
            task_output = executor.output_schema.model_validate(output)
            task.output = task_output.model_dump()

            # TODO Run task executor post-exec hook, if any

            # Save task state
            logger.debug(f"Completed task {task.name}!")
            task.state = TaskStateEnum.completed
            db.add(task)
            db.commit()

            # Write output to message bus for children tasks
            await self._put_task_output(task)

            return task

    async def _get_task_inputs(self, task: TaskInstance) -> dict:
        """Get Task inputs (i.e. outputs from parent tasks) from message bus."""

        # TODO nats interface refactor -- not clean here
        logger.debug(
            f"Getting task {task.name}'s dependencies' outputs: `{task.depends_on}`"
        )

        task_inputs = []
        for dep in task.depends_on:
            input_queue = NATSQueue(
                connection=self.nc,
                stream="jobs",
                subject=f"jobs.{task.state_instance_id}.from_{dep}.to_descendant",
            )
            await input_queue.connect()
            msg = await input_queue.dequeue()
            message = Message.model_validate_json(msg.data)
            task_inputs.append(message.payload)
            await msg.ack()

        # Merge all dicts
        input = dict(ChainMap(*task_inputs))

        return input

    async def _put_task_output(self, task: TaskInstance):
        """Write Task output into message bus for input to any children Tasks."""

        logger.debug(f"Writing task {task.name}'s output")

        # TODO refactor
        output_queue = NATSQueue(
            connection=self.nc,
            stream="jobs",
            subject=f"jobs.{task.state_instance_id}.from_{task.name}.to_descendant",
        )
        await output_queue.connect()

        msg = Message(source=task.name, payload=task.output)
        await output_queue.enqueue(msg.model_dump_json())
