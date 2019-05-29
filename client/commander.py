import queue
from threading import Thread

from client.processor import Processor
from tools.ws_wrapper import Connection
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
        self.connection = Thread(target=Connection, args=('localhost', bot['id'] + 1000, self.orders_queue, self.listener.output_queue, bot))
        self.connection.start()

    def run(self):
        while 1:
            strategy = self.strategies_queue.get()
            tactic = self.processor.create_tactic(strategy)
            self.execute_tactic(tactic)

    def execute_tactic(self, tactic):
        for (order, expected_result) in tactic:
            #  Possible orders:
            #   - Transmit: send the order to the API
            #   - Wait for: just wait for the expected game state without doing anything beforehand.
            # For example waiting for your turn in combat or waiting for an exchange request after entering a map.
            #   - Reevaluate tactic: adapt the plan according to the changing game state.
            # For example, a reevaluation is necessary after performing an FM action depending on the result of this FM.

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
