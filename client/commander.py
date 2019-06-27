import queue
from threading import Thread

from tools.ws_connector import Connection
from client.listener import Listener
from tools import logger
import strategies


class Commander:
    def __init__(self, bot_profile, strategies_queue: queue.Queue, reports_queue: queue.Queue, assets):
        self.bot = bot_profile
        self.logger = logger.get_logger(__name__, self.bot['name'])
        self.strategies_queue = strategies_queue
        self.reports_queue = reports_queue
        self.assets = assets
        self.logger.info('Starting listener')
        self.listener = Listener(self.bot)
        self.listener_thread = Thread(target=self.listener.run)
        self.listener_thread.start()
        self.logger.info('Starting connector')
        self.orders_queue = queue.Queue()
        # self.connection = Thread(target=Connection, args=('localhost', self.bot['id'] + 1000, self.orders_queue, self.listener.output_queue, self.bot))
        self.connection = Thread(target=Connection, args=('176.189.10.164', 8887, self.orders_queue, self.listener.output_queue, self.bot))
        self.connection.start()
        self.logger.info('New commander spawned for {}'.format(self.bot['name']))
        self.run()

    def run(self):
        while 1:
            strategy = self.strategies_queue.get()
            self.logger.info('Received strategy from swarm node: {}'.format(strategy))
            self.execute_strategy(strategy)

    def execute_strategy(self, strategy):
        kwargs = {'strategy': strategy, 'listener': self.listener, 'orders_queue': self.orders_queue, 'assets': self.assets}
        report = strategy
        if hasattr(strategies, strategy['command']) and hasattr(getattr(strategies, strategy['command']), strategy['command']):
            self.logger.info('Starting executor for strategy: {}'.format(strategy))
            report = getattr(getattr(strategies, strategy['command']), strategy['command'])(**kwargs)
        else:
            self.logger.warn('No known strategy named \'{}\''.format(strategy['command']))
            report['report'] = {
                'success': False,
                'details': 'No known strategy named \'{}\''.format(strategy['command'])
            }

        self.logger.info('Sending back report to swarm node: {}'.format(report))
        self.reports_queue.put(report)

    def send_order(self, order):
        self.logger.info('Sending order to bot API: {}'.format(order))
        self.orders_queue.put((order, ))


if __name__ == '__main__':
    bot = {'id': 0, 'name': 'Ilancelet'}
    order = {
        'version': 1,
        'command': 'Close',
    }
    strats = queue.Queue()
    commander = Commander(bot, strats)
    commander.send_order(order)
