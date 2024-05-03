import asyncio
import time

from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session
import attr

from germinate_ai.message_bus import nats
from germinate_ai.message_bus.message_queue import NATSQueue
from germinate_ai.data.schemas.tasks import TaskAssignment
from germinate_ai.data.repositories.states_repository import get_state
from germinate_ai.data.repositories.workflow_runs_repository import get_workflow_run
from germinate_ai.data.models import StateInstanceStateEnum
from germinate_ai.data.schemas.workflow_runs import WorkflowRunStateEnum
from germinate_ai.data.models import StateInstance
from germinate_ai.utils.helpers import get_next_tick
from germinate_ai.data.schemas.messages import Message

from .scheduler import Scheduler


@attr.define(init=False)
class Coordinator:
    """Polls task completions and updates corresponding state."""

    nc: nats.NatsConnection
    db: Session
    tick_interval: int
    scheduler: Scheduler
    completions_queue: NATSQueue

    def __init__(
        self, nc: nats.NatsConnection, db: Session, scheduler: Scheduler, tick_interval: int = 10
    ):
        self.nc = nc
        self.db = db
        self.tick_interval = tick_interval
        self.scheduler = scheduler

    async def run(self):
        """Connect to message bus, wait for task completion notifications, and update state/schedule tasks accordingly."""

        next_tick = get_next_tick(self.tick_interval)

        await self.connect()
        logger.success(
            "Coordinator connected to cluster! Waiting for task completions..."
        )

        while True:
            last_tick = time.time()

            try:
                msg = await self.completions_queue.dequeue()
                task_json = msg.data
                # ack message so we don't see it again
                await msg.ack()
                await self._handle_task_completion(task_json)                    
            except TimeoutError:
                pass
            except asyncio.CancelledError:
                logger.debug(
                    "Worker #{self.id}: Cancelled! Shutting down coordinator..."
                )
                break
            except Exception as e:
                logger.exception("Error while reading from NATS queue: ", e)

            await asyncio.sleep(next_tick(last_tick=last_tick))

    async def connect(self):
        """Connect to get task completion notifications."""
        self.completions_queue = NATSQueue(
            stream="jobs",
            subject="jobs.task_completions",
            durable_consumer="coordinator",
            connection=self.nc,
        )
        await self.completions_queue.connect()

        await self.scheduler.connect()

    async def _handle_task_completion(self, task_json: str) -> bool:
        # TODO too long - refactor!!

        try:
            logger.debug(f"Handling message: `{task_json}`")
            assignment = TaskAssignment.model_validate_json(task_json)
        except ValidationError as e:
            logger.error(f"Skipping invalid task `{task_json}`: {e}")
            return True

        # # Get corresponding Task from DB
        # task = get_task_instance_from_assignment(self.db, assignment)
        # if task is None:
        #     logger.error(f"No such task: skipping `{assignment}`")
        #     return True

        # Get corresponding State from DB
        state_instance = get_state(self.db, assignment.state_instance_id)
        if state_instance is None:
            logger.error(f"Skipping invalid state_instance `{assignment.state_instance_id}`")
            return
        
        # Is current phase still incomplete?
        if not state_instance.current_phase_complete:
            # More tasks remaining in this state phase, so don't do anything
            return True
    
        # Are there unscheduled phases remaining in this state?
        if not state_instance.all_phases_complete:
            logger.debug(f"Queuing next phases in state {state_instance.name} complete.")
            # Enqueue next phase and return
            state_instance.next_phase()
            await self._enqueue_state_phase(state_instance)
            return True


        # All tasks in state's tasks DAG are complete!
        logger.debug(f"State {state_instance.name} completed!")
        if state_instance.state == StateInstanceStateEnum.completed:
            logger.debug(f"Looks like {state_instance.name} was already marked as completed. Skipping...")
            return
        
        

        # Get workflow run
        workflow_run = get_workflow_run(self.db, state_instance.workflow_run_id)

        # Figure out transition to next state
        # (Uses condition evaluation results from DB)
        next_state_name = state_instance.next_state()
        if next_state_name is None:
            # Update workflow run state and finish
            
            # TODO refactor
            
            # Completed workflow
            logger.success(f"Workflow run {workflow_run.workflow_name}#v{workflow_run.workflow_version} completed!")
            
            # Combine output from final phase of last state
            final_output = state_instance.state_output()
            # Save it in workflow run entry
            workflow_run.output = final_output

            workflow_run.state = WorkflowRunStateEnum.completed
            self.db.add(workflow_run)
            
            # Update state instance state
            state_instance.state = StateInstanceStateEnum.completed
            self.db.add(state_instance)
            self.db.commit()
            
            return


        logger.debug(f"Transition from {state_instance.name} to {next_state_name}")

        # get next state instance
        next_state_instance = workflow_run.state_instance_by_name(next_state_name)

        # Get combined output from prev state for next state's input
        next_state_input = state_instance.state_output()
        # print(next_state_input)
    
        # TODO refactor
        # store input to first phase tasks
        nq = NATSQueue(
            connection=self.nc,
            stream="jobs",
            subject=f"jobs.{next_state_instance.id}.from_start.to_descendant",
        )
        await nq.connect()
        msg = Message(source="start", payload=next_state_input)
        await nq.enqueue(msg.model_dump_json())
        #

        # Update state instance state
        state_instance.state = StateInstanceStateEnum.completed
        self.db.add(state_instance)

        # Transition workflow run to next state
        workflow_run.current_state = next_state_instance
        self.db.add(workflow_run)
        self.db.commit()

        # Enqueue the first phase in new state
        await self._enqueue_state_phase(next_state_instance)


    async def _enqueue_state_phase(self, state: StateInstance):
        # Enter next phase in state
        await self.scheduler.enqueue_tasks(state.phase_tasks)
        # update state instance
        self.db.add(state)
        self.db.commit()