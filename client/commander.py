import json
import os
import traceback
from random import randint
import socket
import queue
from threading import Thread
from subprocess import Popen, PIPE
import time

from tools.ws_connector import Connection
from client.listener import Listener
from tools import logger
import strategies
import hashlib


class Commander:
    def __init__(self, bot_profile, strategies_queue: queue.Queue, reports_queue: queue.Queue, assets):
        self.bot = bot_profile
        self.logger = logger.get_logger(__name__, self.bot['name'])
        self.strategies_queue = strategies_queue
        self.reports_queue = reports_queue
        self.assets = assets
        self.logger.info('Starting LL API')
        self.port = randint(10000, 20000)
        while not self.try_port(self.port):
            self.port = randint(10000, 20000)
        args = ['java', '-jar', os.path.join(os.path.dirname(__file__), '..', 'black-falcon-api-1.0-jar-with-dependencies.jar'), '-p', str(self.port)]
        Popen(' '.join(args), shell=True)
        time.sleep(5)
        self.logger.info('Starting listener')
        self.listener = Listener(self.bot, self.assets)
        self.listener_thread = Thread(target=self.listener_bootstrapper)
        self.listener_thread.start()
        self.logger.info('Starting connector')
        self.orders_queue = queue.Queue()
        self.connection_crashed = [False]
        self.connection = Thread(target=self.connection_bootstrapper)
        self.connection.start()
        self.logger.info('New commander spawned for {}'.format(self.bot['name']))
        Thread(target=self.interrupts).start()
        self.run()
        self.logger.info('Commander shut down')

    def run(self):
        while 1:
            strategy = self.strategies_queue.get()
            if 'stop' in strategy.keys():
                # Kill the commander
                self.logger.info('Shutting down...')

                # Stop the listener
                self.logger.info('Shutting down listener')
                self.listener.stop = True

                # Stop the connector
                self.logger.info('Shutting down connector')
                self.orders_queue.put((json.dumps({'command': 'conn_shutdown'}), ))

                Thread(target=strategies.support_functions.update_profile, args=(self.bot['name'], 'connected', False)).start()
                logger.close_logger(self.logger)
                break
            else:
                # Business as usual
                self.logger.info('Received strategy from swarm node: {}'.format(strategy))
                self.execute_strategy(strategy)

    def listener_bootstrapper(self):
        try:
            self.listener.run()
        except Exception:
            report = {
                'exception_notif': 'listener',
                'traceback': traceback.format_exc(),
                'bot': self.bot['name']
            }
            self.reports_queue.put((report,))

    def connection_bootstrapper(self):
        try:
            Connection('localhost', self.port, self.orders_queue, self.listener.output_queue, self.bot)
        except:
            print('################' + 'Connection creashed')
            report = {
                'exception_notif': 'connection',
                'traceback': traceback.format_exc(),
                'bot': self.bot['name']
            }
            self.reports_queue.put((report,))

    def execute_strategy(self, strategy):
        kwargs = {'strategy': strategy, 'listener': self.listener, 'orders_queue': self.orders_queue, 'assets': self.assets}
        report = strategy
        if hasattr(strategies, strategy['command']) and hasattr(getattr(strategies, strategy['command']), strategy['command']):
            self.logger.info('Starting executor for strategy: {}'.format(strategy))
            try:
                report = getattr(getattr(strategies, strategy['command']), strategy['command'])(**kwargs)
            except Exception:
                self.logger.error('Executor for {} crashed'.format(strategy))
                report.update({
                    'exception_notif': 'Strategy',
                    'traceback': traceback.format_exc(),
                    'bot': self.bot['name']
                })
        else:
            self.logger.warn('No known strategy named \'{}\''.format(strategy['command']))
            report['report'] = {
                'success': False,
                'details': 'No known strategy named \'{}\''.format(strategy['command'])
            }

        self.logger.info('Sending back report to swarm node: {}'.format(report))
        self.reports_queue.put(report)

    def try_port(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = False
        try:
            sock.bind(("localhost", port))
            result = True
        except:
            pass
        sock.close()
        return result

    def interrupts(self):
        last_file_request_message = 0
        while 1:
            time.sleep(0.1)
            if self.listener.game_state['file_request_message']['timestamp'] != last_file_request_message:
                last_file_request_message = self.listener.game_state['file_request_message']['timestamp']

                file_name_hash = hashlib.md5(self.listener.game_state['file_request_message']['filename'].encode('utf-8')).hexdigest()

                if self.listener.game_state['file_request_message']['type'] == 0:
                    value = self.assets['hashes_and_sizes'][self.listener.game_state['file_request_message']['filename'].split('/')[-1].replace('.', '')]['size']
                else:
                    value = self.assets['hashes_and_sizes'][self.listener.game_state['file_request_message']['filename'].split('/')[-1].replace('.', '')]['md5']

                order = {
                    "command": "check_file_message",
                    "parameters": {
                        "filenameHash": file_name_hash,
                        "type": self.listener.game_state['file_request_message']['type'],
                        "value": value
                    }
                }
                self.orders_queue.put((json.dumps(order),))


if __name__ == '__main__':
    pass
