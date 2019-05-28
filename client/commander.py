from queue import Queue
from threading import Thread

from client.ws_wrapper import Connection
from client.listener import Listener
from tools import logger


class Commander:
    def __init__(self, bot):
        self.logger = logger.get_logger(__name__, bot['name'])
        self.bot = bot
        self.logger.info('Starting listener')
        self.listener = Listener(bot)
        self.orders_queue = Queue()
        self.logger.info('Starting connector')
        self.connection = Thread(target=Connection, args=(bot, self.orders_queue, self.listener.output_queue))
        self.connection.start()

    def send_order(self, processed_order):
        self.orders_queue.put((processed_order, ))


if __name__ == '__main__':
    bot = {'id': 0, 'name': 'Ilancelet'}
    order = {
        'version': 1,
        'command': 'Close',
    }
    commander = Commander(bot)

    commander.send_order(order)
