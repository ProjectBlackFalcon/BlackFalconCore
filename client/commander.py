import queue
from threading import Thread

from client.processor import Processor
from client.ws_wrapper import Connection
from client.listener import Listener
from tools import logger


class Commander:
    def __init__(self, bot, strategies_queue: queue.Queue):
        self.logger = logger.get_logger(__name__, bot['name'])
        self.bot = bot
        self.strategies_queue = strategies_queue
        self.logger.info('Starting processor')
        self.processor = Processor()
        self.logger.info('Starting listener')
        self.listener = Listener(bot)
        self.logger.info('Starting connector')
        self.orders_queue = queue.Queue()
        self.connection = Thread(target=Connection, args=(bot, self.orders_queue, self.listener.output_queue))
        self.connection.start()

    def run(self):
        while 1:
            strategy = self.strategies_queue.get()
            tactic = self.processor.create_tactic(strategy)
            self.execute_tactic(tactic)

    def execute_tactic(self, tactic):
        for (order, expected_result) in tactic:
            self.send_order(order)
            success, acutal_result = self.validate_result(expected_result)
            if not success:
                self.logger.warn('Order unsuccessful. Order: {}, Expected result: {}, Actual result {}'.format(order, expected_result, acutal_result))
                break

    def send_order(self, order):
        self.orders_queue.put((order, ))

    def validate_result(self, expected_result):
        return False, None


if __name__ == '__main__':
    bot = {'id': 0, 'name': 'Ilancelet'}
    order = {
        'version': 1,
        'command': 'Close',
    }
    strats = queue.Queue()
    commander = Commander(bot, strats)
    commander.send_order(order)
