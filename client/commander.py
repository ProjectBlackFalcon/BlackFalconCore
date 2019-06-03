import ast
import queue
import time
from threading import Thread

from client.processor import Processor
from tools.ws_wrapper import Connection
from client.listener import Listener
from tools import logger


class Commander:
    def __init__(self, bot, strategies_queue: queue.Queue, reports_queue: queue.Queue):
        self.logger = logger.get_logger(__name__, bot['name'])
        self.bot = bot
        self.strategies_queue = strategies_queue
        self.reports_queue = reports_queue
        self.logger.info('Starting processor')
        self.processor = Processor()
        self.logger.info('Starting listener')
        self.listener = Listener(bot)
        self.logger.info('Starting connector')
        self.orders_queue = queue.Queue()
        self.connection = Thread(target=Connection, args=('localhost', bot['id'] + 1000, self.orders_queue, self.listener.output_queue, bot))
        self.connection.start()
        Thread(target=self.listener.run).start()
        self.run()

    def run(self):
        while 1:
            strategy = self.strategies_queue.get()
            self.logger.info('Received strategy: {}'.format(strategy))
            self.execute_strategy(strategy)

    def execute_strategy(self, strategy):
        if strategy['command'] == 'ping':
            self.logger.info('Executing ping strategy')
            last_ping = self.listener.game_state['ping'] if 'ping' in self.listener.game_state.keys() else 0
            print('Last ping: ', last_ping)
            self.send_order('ping')
            waiting = True
            while waiting:
                if 'ping' in self.listener.game_state.keys():
                    if last_ping != self.listener.game_state['ping']:
                        waiting = False
                time.sleep(0.1)
            self.logger.info('Received pong response')
            strategy['report'] = True
            self.reports_queue.put(strategy)

    def send_order(self, order):
        self.logger.info('Sending order : {}'.format(order))
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
