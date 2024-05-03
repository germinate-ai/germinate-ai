import asyncio

from germinate_ai.data.database import get_db_session
from germinate_ai.message_bus import nats

from .coordinator import Coordinator
from .scheduler import Scheduler


async def run_coordinator():
    loop = asyncio.get_running_loop()
    Session = get_db_session()
    with Session() as db_session:
        async with nats.nats_connection() as nc:
            scheduler = Scheduler(nc=nc)

            coordinator = Coordinator(nc=nc, db=db_session, scheduler=scheduler)
            coordinator_task = loop.create_task(coordinator.run())

            tasks = [coordinator_task]

            await asyncio.gather(*tasks)


def start_coordinator():
    asyncio.run(run_coordinator())
