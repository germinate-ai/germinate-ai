import pytest

from germinate_ai.message_bus.nats import nats_connection
from germinate_ai.message_bus.message_queue import NATSQueue


@pytest.fixture
async def nats_queue():
    nq = NATSQueue("test", "test.test", "test_consumer")
    await nq.connect()
    return nq


@pytest.mark.asyncio
async def test_nats_queue_connect(nats_queue):
    """Connect and see that connections attributes are not None."""
    nq = await nats_queue

    print(nq)

    assert nq.connection is not None
    assert nq.connection.nc is not None
    assert nq.connection.jetstream is not None
    assert nq.consumer is not None

    await nq.connection.close()


@pytest.mark.asyncio
async def test_nats_queue_enqueue_dequeue(nats_queue):
    """Add an item and take it out."""
    nq = await nats_queue

    await nq.enqueue("test")

    msg = await nq.dequeue()
    data = msg.data
    assert data == "test"

    await msg.ack()
    await nq.connection.close()


@pytest.fixture
def test_queue_data():
    return ["test1", "test2", "test3"]


@pytest.mark.asyncio
async def test_nats_queue_aiter_dequeue(nats_queue, test_queue_data):
    """Put in and take out 3 items."""
    nq = await nats_queue

    for v in test_queue_data:
        await nq.enqueue(v)

    ix = 0
    while ix < 3:
        async for item in nq.aiter_dequeue():
            assert test_queue_data[ix] == item.data
            ix += 1

    await nq.connection.close()
