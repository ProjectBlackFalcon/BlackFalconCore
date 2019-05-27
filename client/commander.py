from client import listener, dummy_api
import asyncio
import websockets
from threading import Thread
import time

class Commander:
    def __init__(self, bot: dict):
        self.bot = bot
        self.api = dummy_api
        self.new_order = False
        self.order = None
        Thread(target=dummy_api.start_server, args=(self.bot['id'], )).start()
        self.connection = asyncio.get_event_loop().run_until_complete(websockets.connect('ws://localhost:{}'.format(self.bot['id'] + 1000)))
        asyncio.get_event_loop().run_until_complete(self.handler())

    async def handler(self):
        consumer_task = asyncio.ensure_future(self.consumer_handler())
        producer_task = asyncio.ensure_future(self.producer_handler())
        done, pending = await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def consumer_handler(self):
        while True:
            message = await self.connection.recv()
            await self.consumer(message)

    async def producer_handler(self):
        while True:
            message = await self.producer()
            await self.connection.send(message)

    async def consumer(self, message):
        print(message)

    async def producer(self):
        while not self.new_order:
            time.sleep(0.1)
        self.new_order = False
        return self.order

    def send_order(self, order):
        self.order = order
        self.new_order = True

if __name__ == '__main__':
    commander = Commander({'id': 0})
    order = {
        'version': 1,
        'command': 'Close',
    }
    commander.send_order(str(order).encode('utf8'))
    time.sleep(1)
    commander.send_order(str(order).encode('utf8'))

