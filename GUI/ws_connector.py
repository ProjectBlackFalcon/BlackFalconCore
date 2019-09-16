import json
import queue

import websocket
from threading import Thread

import time

import logger


class Connection:
    def __init__(self, host, port, orders_queue, output_queue, bot=None):
        self.stop = [False]
        self.host = host
        self.port = port
        self.logger = logger.get_logger(__name__, 'Connection-{}-{}'.format(host, port) if bot is None else bot['name'])
        self.orders_queue = orders_queue
        self.output_queue = output_queue
        self.connection_string = 'ws://{}:{}'.format(host, port)
        self.logger.info('Connecting to websocket at: ' + self.connection_string)
        self.connection = websocket.WebSocketApp(self.connection_string, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.connection.run_forever(ping_interval=15)
        if not self.stop[0]:
            raise Exception("Websocket at {} closed unexpectedly".format(self.connection_string))

    def on_message(self, message):
        self.logger.info('Recieved message from API: ' + message)
        self.output_queue.put((message, ))

    def on_error(self, error):
        self.logger.error(error)

    def on_close(self):
        if self.stop[0]:
            self.logger.info("Websocket at {} closed successfully".format(self.connection_string))
            logger.close_logger(self.logger)
        else:
            self.logger.error("Websocket at {} closed unexpectedly".format(self.connection_string))
            logger.close_logger(self.logger)

    def on_open(self):
        self.logger.info('Connection established to websocket at ' + self.connection_string + ', ready to send orders')

        def run(queue):
            while 1:
                for order in queue.get():
                    if json.loads(order)['command'] == 'conn_shutdown':
                        self.stop = [True]  # Using a mutable so it carries its value outside the thread
                    self.logger.info('Sending order: ' + str(order))
                    self.connection.send(str(order).encode('utf8'))
                if self.stop == [True]:
                    break
            self.logger.info('Websocket connection shutting down')
            self.connection.close()

        Thread(target=run, args=(self.orders_queue, )).start()


if __name__ == '__main__':
    pass
