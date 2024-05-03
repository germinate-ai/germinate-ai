import asyncio
import os
from concurrent.futures import ProcessPoolExecutor

from loguru import logger

from germinate_ai.message_bus import nats
from germinate_ai.data.database import get_db_session

from .worker import Worker
from .task_dispatcher import TaskDispatcher

cpu_count = os.cpu_count()


async def run_worker(ix: int):
    """Start a single concurrent `Worker` instance."""
    Session = get_db_session()
    loop = asyncio.get_running_loop()
    async with nats.nats_connection() as nc:
        task_dispatcher = TaskDispatcher(nc=nc, sessionmaker=Session)
        worker = Worker(nc=nc, id=ix, task_dispatcher=task_dispatcher)
        worker_task = loop.create_task(worker.run())
        await worker_task


def run_worker_proc(ix: int):
    """Run a single Worker in its own `asyncio` loop."""
    logger.debug(f"Starting worker process #{ix}...")
    # TODO create m async worker tasks
    asyncio.run(run_worker(ix))


def start_worker_node(n_procs: int):
    """Launch the worker node with `n_procs` processes."""
    if n_procs == -1:
        logger.debug(f"Launching cpu_count={cpu_count} worker processes...")
        n_procs = cpu_count
    if n_procs is None:
        n_procs = 2

    loop = asyncio.new_event_loop()
    with ProcessPoolExecutor(max_workers=n_procs) as pool:
        tasks = [
            loop.run_in_executor(pool, run_worker_proc, ix) for ix in range(n_procs)
        ]
        logger.info(f"Started {n_procs} worker processes...")

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Stopping...")
        for t in tasks:
            t.cancel()
        logger.info("Waiting for worker processes to shut down...")
        closing = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(closing)
        loop.close()
