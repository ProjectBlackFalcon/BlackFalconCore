import queue
import time

import websocket
from threading import Thread

from credentials import credentials
from tools import logger


class Connection:
    def __init__(self, host, port, orders_queue, output_queue, bot=None):
        self.logger = logger.get_logger(__name__, bot['name'] if bot is not None else 'Connection-{}-{}'.format(host, port))
        self.orders_queue = orders_queue
        self.output_queue = output_queue
        self.connection_string = 'ws://{}:{}'.format(host, port)
        self.logger.info('Connecting to websocket at: ' + self.connection_string)
        self.connection = websocket.WebSocketApp(self.connection_string, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.connection.on_open = self.on_open
        self.connection.run_forever()

    def on_message(self, message):
        self.logger.info('Recieved message from API: ' + message)
        self.output_queue.put((message, ))

    def on_error(self, error):
        self.logger.error(error)

    def on_close(self):
        self.logger.info("Websocket closed")

    def on_open(self):
        self.logger.info('Connection established to websocket at ' + self.connection_string)

        def run(queue):
            while 1:
                for order in queue.get():
                    self.logger.info('Sending order: ' + str(order))
                    self.connection.send(str(order).encode('utf8'))
        Thread(target=run, args=(self.orders_queue, )).start()


if __name__ == '__main__':
    orders = queue.Queue()
    t = Thread(target=Connection, args=('localhost', 8721, orders, queue.Queue()))
    t.start()
    order = {
        'bot': credentials['bots']['0'],
        'command': 'ping',
        'version': 1,
        'parameters': None
    }
    orders.put((order, ))
    print('Order sent')
    time.sleep(10)
    orders.put((order,))
    print('Order sent')