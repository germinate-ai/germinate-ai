import asyncio
import time

from loguru import logger
from nats.errors import TimeoutError
from nats.js.api import ConsumerConfig, DeliverPolicy

from .connection import NatsConnection


class NatsPullConsumer:
    """Connect to a NATS durable pull consumer and use an async generator to get raw messages from it."""

    def __init__(self, subject: str, stream: str, durable: str, nc: NatsConnection):
        self.subject = subject
        self.stream = stream
        self.durable = durable
        self.nc = nc
        self.consumer = None

    async def connect(self):
        logger.debug(f"Creating durable consumer: `{self.durable}`...")
        self.consumer = await self.nc.jetstream.pull_subscribe(
            self.subject,
            stream=self.stream,
            durable=self.durable,
            # TODO
            config=ConsumerConfig(deliver_policy=DeliverPolicy.NEW),
        )

    async def messages(self, batch_size=1, ack=True):
        msgs = await self.consumer.fetch(batch=batch_size)
        for msg in msgs:
            yield msg
            # acknowledge msg
            if ack:
                await msg.ack()


async def consume_nats_messages(consumer: NatsPullConsumer, tick_interval=10):
    """Check for new messages using `consumer` every `tick_interval` seconds."""

    # Move to node
    def next_tick(last_tick: float):
        time_since = time.time() - last_tick
        return tick_interval - time_since

    logger.trace(f"Polling messages every {tick_interval}s...")
    while True:
        last_tick = time.time()

        try:
            async for msg in consumer.messages():
                # decode message
                decoded_msg = msg.data.decode()
                logger.info(f"Got message: `{decoded_msg}`")
                yield decoded_msg
        except TimeoutError:
            # logger.debug("nats timeout")
            # print(".", end="")
            pass
        except Exception as e:
            logger.exception("Error reading from NATS: ", e)
        
        # logger.debug("sleeping till next tick...")
        await asyncio.sleep(next_tick(last_tick=last_tick))
