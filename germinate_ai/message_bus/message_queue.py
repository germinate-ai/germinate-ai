from abc import ABC, abstractmethod
from typing import TypeVar, Generic, AsyncGenerator

from nats.aio.msg import Msg

from .nats import NatsConnection


T = TypeVar("T", bound=str)


class AbstractMessageQueue(Generic[T], ABC):
    """Abstract message queue."""

    @abstractmethod
    async def enqueue(self, item: T):
        pass

    @abstractmethod
    async def dequeue(self) -> T:
        pass


class NATSQueue(AbstractMessageQueue[Generic[T]], ABC):
    """A distributed message queue on top of NATS Jetstream."""

    def __init__(
        self,
        stream: str,
        subject: str,
        durable_consumer: str = None,
        connection: NatsConnection = None,
    ):
        if connection is None:
            connection = NatsConnection()
        self.connection = connection
        self.stream = stream
        self.subject = subject
        self.durable_consumer = durable_consumer
        self.consumer = None

    async def connect(self):
        if not self.connection.is_connected:
            await self.connection.connect()
        # if self.durable_consumer is not None:
        self.consumer = await self.connection.jetstream.pull_subscribe(
            stream=self.stream,
            subject=self.subject,
            durable=self.durable_consumer,
        )

    async def enqueue(self, item: T):
        await self.connection.jetstream.publish(self.subject, item.encode())

    async def dequeue(self) -> Msg:
        # Callers are responsible for acknowledging with `await msg.ack()` call!!
        msgs = await self.consumer.fetch(batch=1)
        for msg in msgs:
            msg.data = msg.data.decode()
            return msg

    async def aiter_dequeue(self) -> AsyncGenerator[T, None]:
        msgs = await self.consumer.fetch(batch=1)
        for msg in msgs:
            # bytes -> str
            msg.data = msg.data.decode()
            yield msg
            await msg.ack()
