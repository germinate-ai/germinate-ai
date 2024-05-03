import typing as typ

from nats.aio.msg import Msg
from nats.js import JetStreamContext

from .nats.connection import NatsConnection


class AbstractMessageChannel:
    """Abstract Message Channel."""

    connected: bool = False

    def __init__(
        self,
        stream: str,
        subject: str,
        durable_consumer: str = None,
        connection: NatsConnection = None,
    ):
        self.subject = subject
        if connection is None:
            connection = NatsConnection()
        self.connection = connection
        self.stream = stream
        self.durable_consumer = durable_consumer

    async def connect(self):
        """Connect to the message bus."""
        if not self.connection.is_connected:
            await self.connection.connect()
        self.connected = True


def _validate_write_subject(subject: str) -> bool:
    """Check that subjects for write channels don't have wildcards *, >."""
    subject_chars = set(subject)
    invalid = "*" in subject_chars or ">" in subject_chars
    return not invalid


class ROMessageChannel(AbstractMessageChannel):
    """A Read Only Message Channel"""

    consumer: JetStreamContext.PullSubscription

    async def connect(self):
        """Connect to the message bus."""
        await super().connect()
        self.consumer = await self.connection.jetstream.pull_subscribe(
            stream=self.stream,
            subject=self.subject,
            durable=self.durable_consumer,
        )

    async def read(self, batch: int = 1) -> typ.Sequence[Msg]:
        """Read `batch` messages from the channel."""
        if not self.connected:
            await self.connect()
        msgs = await self.consumer.fetch(batch=batch)
        for msg in msgs:
            msg.data = msg.data.decode()
        return msgs


class WOMessageChannel(AbstractMessageChannel):
    "A Write Only Message Channel"

    def __init__(
        self,
        stream: str,
        subject: str,
        durable_consumer: str = None,
        connection: NatsConnection = None,
    ):
        if not _validate_write_subject(subject):
            raise ValueError(f"Invalid subject {subject} for write channel")

        self.subject = subject
        if connection is None:
            connection = NatsConnection()
        self.connection = connection
        self.stream = stream
        self.durable_consumer = durable_consumer

    async def write(self, msg: str):
        """Write the string `msg` into the message bus."""
        await self.connection.jetstream.publish(self.subject, msg.encode())


class RWMessageChannel(WOMessageChannel, ROMessageChannel):
    "A Read/Write Message Channel"

    pass
