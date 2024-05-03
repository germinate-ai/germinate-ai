import asyncio
import typing as typ
from types import ModuleType

from loguru import logger
from pydantic import BaseModel, ValidationError

from germinate_ai.coordinator import Scheduler
from germinate_ai.core.exceptions import InvalidArgumentsException
from germinate_ai.core.loader import (
    get_workflow_from_module,
    import_module,
    parse_import_path,
)
from germinate_ai.core.workflows import Workflow
from germinate_ai.data.database import get_db_session
from germinate_ai.data.models import (
    StateInstance,
    StateInstanceStateEnum,
    TaskInstance,
    WorkflowRunStateEnum,
)
from germinate_ai.data.repositories.workflow_runs_repository import (
    create_run_from_workflow,
)
from germinate_ai.data.schemas.messages import Message
from germinate_ai.message_bus import NATSQueue, nats_connection


def import_and_run_workflow(
    workflow_import_path: str,
    *,
    working_dir: typ.Optional[str] = None,
    input_data_json: typ.Optional[str] = None,
):
    module_name, var_name = parse_import_path(workflow_import_path)
    module = import_module(module_name, working_dir=working_dir)
    workflow = get_workflow_from_module(module, var_name=var_name)

    logger.info(f"Running workflow {workflow.name}")
    run_workflow(workflow, module, input_data_json)


def run_workflow(workflow: Workflow, module: ModuleType, input_data_json: str):
    # 1. sort each state's task DAG
    workflow.build()
    # print("BUILT")
    # import sys
    # sys.exit(0)

    state_phases = {}
    for state in workflow.states:
        state.validate()
        state_phases[state.name] = state.sorted_tasks_dag()

    # Some sanity checks:

    # TODO temp - only allow one root state
    _initial_state_phase = state_phases[workflow.initial_state.name][0]
    assert (
        len(_initial_state_phase) == 1
    ), "There should only be one starting task in DAG"

    # Check the inputted json matches the input schema
    _initial_task_name = _initial_state_phase[0]
    initial_task = next(
        t for t in workflow.initial_state.tasks if t.name == _initial_task_name
    )
    input_schema = initial_task.executor.input_schema
    try:
        input_data = input_schema.model_validate_json(input_data_json)
    except ValidationError as e:
        raise InvalidArgumentsException(
            f"Invalid input data for root task(s) in initial state: {e}"
        )


    # 2. Create DB entries (in txn)
    Session = get_db_session()
    with Session() as db:
        with db.begin():
            # Create a workflow run
            workflow_run = create_run_from_workflow(db, workflow)
            workflow_run.state = WorkflowRunStateEnum.in_progress
            # workflow_run.workflow_state_machine = workflow

            # Create each state in workflow
            initial_state = None
            for state in workflow.states:
                state_instance = StateInstance(
                    name=state.name, workflow_run=workflow_run
                )
                # Store toposorted generations
                state_instance.sorted_tasks_phases = state_phases[state.name]

                # Note initial state
                if state == workflow.initial_state:
                    state_instance.state = StateInstanceStateEnum.queued
                    initial_state = state_instance

                # Create each task in each state
                for task in state.tasks:
                    task_instance = TaskInstance(
                        name=task.name,
                        state_instance=state_instance,
                    )
                    # TODO
                    task_instance.task_executor_name = task.executor.registered_name
                    # task_instance.task_executor = task
                    # mark first state as depending on "start" so it gets the input
                    # from the outputs channel
                    # if task == initial_task:
                    
                    # mark first phase tasks in each state as depending on a "start" task
                    # -- just a trick to get the task dispatcher to pull the input data
                    #    for the start tasks from the message bus
                    if task.name in state_instance.sorted_tasks_phases[0]:
                        task_instance.depends_on = ["start"]
                    else:
                        task_instance.depends_on = [p.name for p in task.parents]
                    db.add(task_instance)
                
                # Store transition information
                state_transitions = {}
                for condition in state.conditions:
                    state_transitions[condition.name] = condition.transition.target.name
                state_instance.transitions = state_transitions

                db.add(state_instance)


            workflow_run.initial_state_name = initial_state.name
            workflow_run.current_state = initial_state
            db.add(workflow_run)

        db.refresh(initial_state)

        # 3. Queue first phase of initial state
        asyncio.run(_run_state(initial_state, input_data=input_data))


async def _run_state(state: StateInstance, *, input_data: BaseModel):
    async with nats_connection() as nc:
        # store input to first phase tasks
        nq = NATSQueue(
            connection=nc,
            stream="jobs",
            subject=f"jobs.{state.id}.from_start.to_descendant",
        )
        await nq.connect()
        msg = Message(source="start", payload=input_data.model_dump())
        await nq.enqueue(msg.model_dump_json())

        scheduler = Scheduler(nc=nc)
        await scheduler.connect()
        await scheduler.enqueue_state(state)
