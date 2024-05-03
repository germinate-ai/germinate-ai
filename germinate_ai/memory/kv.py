from nats.js.kv import KeyValue as _KeyValue

from germinate_ai.message_bus.nats import NatsConnection


class KeyValueStore:
    """NATS Key Value Store"""

    connected: bool = False
    kv: _KeyValue = None

    def __init__(self, bucket_name: str, connection: NatsConnection = None):
        self.bucket_name = bucket_name
        if connection is None:
            connection = NatsConnection()
        self.connection = connection
        
    
    async def connect(self):
        """Connect to NATS cluster."""
        if not self.connection.is_connected:
            await self.connection.connect()
        self.kv = await self.connection.jetstream.create_key_value(bucket=self.bucket_name)
        self.connected = True

    async def get(self, key: str) -> str:
        """Get value corresponding to key."""
        entry =  await self.kv.get(key)
        return entry.value.decode()

    async def put(self, key: str, value: str):
        """Store key, value in store.""" 
        await self.kv.put(key, value.encode())


def kv_story_factory(*, bucket_name: str, connection: NatsConnection = None):
    """Creates a KV store."""
    kv = KeyValueStore(bucket_name, connection=connection)
    return kv