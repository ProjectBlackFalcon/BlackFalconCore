import websocket
import _thread as thread
from tools import logger


class Connection:
    def __init__(self, bot: dict, orders_queue, output_queue):
        self.logger = logger.get_logger(__name__, bot['name'])
        self.bot = bot
        self.orders_queue = orders_queue
        self.output_queue = output_queue
        self.connection_string = 'ws://localhost:{}'.format(self.bot['id'] + 1000)
        self.logger.info('Connecting to websocket at: ' + self.connection_string)
        self.connection = websocket.WebSocketApp(self.connection_string, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.connection.on_open = self.on_open
        self.connection.run_forever()

    def on_message(self, message):
        self.logger.info('Recieved message from API' + message)
        self.output_queue.put((message, ))

    def on_error(self, error):
        self.logger.error(error)

    def on_close(self):
        self.logger.info("Websocket closed")

    def on_open(self):
        self.logger.info('Connection established to websocket at ' + self.connection_string)

        def run(queue):
            for order in queue.get():
                self.logger.info('Sending order:' + str(order))
                self.connection.send(str(order).encode('utf8'))
        thread.start_new_thread(run, (self.orders_queue, ))
