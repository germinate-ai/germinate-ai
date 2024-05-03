from contextlib import asynccontextmanager

import nats
from loguru import logger

from germinate_ai.config import settings

NATS_URL = settings.nats_url


class NatsConnection:
    """NATS connection singleton class."""

    _instance: "NatsConnection" = None

    def __new__(cls, nats_url=NATS_URL) -> "NatsConnection":
        if cls._instance is None:
            logger.debug(f"Creating a new NATS connection to cluster: `{nats_url}`...")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, nats_url=NATS_URL):
        self.nats_url = nats_url
        self.nc = None
        self.jetstream = None

    @property
    def is_connected(self) -> bool:
        if self.nc is None:
            return False
        return self.nc.is_connected

    async def connect(self):
        # Connect if necessary
        if self.nc is None:
            self.nc = await nats.connect(self.nats_url)
        # Jetstream context
        if self.jetstream is None:
            self.jetstream = self.nc.jetstream()

    async def close(self):
        await self.nc.close()


@asynccontextmanager
async def nats_connection(nats_url=NATS_URL):
    """NATS connection context manager that opens and closes the connection for you."""
    nc = NatsConnection(nats_url=nats_url)
    await nc.connect()
    yield nc
    await nc.close()
