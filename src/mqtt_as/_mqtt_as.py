import asyncio

config = {}


class MQTTClient:
    DEBUG = False

    def __init__(self, config):
        self.config = config
        self.up = asyncio.Event()
        self.queue = asyncio.Queue()

    async def connect(self):
        pass

    async def publish(self, topic, payload, qos):
        pass

    async def subscribe(self, topic, qos):
        pass

    async def close(self):
        pass
