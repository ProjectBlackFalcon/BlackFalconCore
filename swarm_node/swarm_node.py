import ast
import json
import queue
import time
import uuid
from threading import Thread

from websocket_server import WebsocketServer

from client.commander import Commander
from tools import logger


class SwarmNode:
    def __init__(self, host):
        self.logger = logger.get_logger(__name__, 'swarm_node')
        self.host = host
        self.api_port = 8721
        self.api = WebsocketServer(self.api_port, host=self.host)
        self.api.set_fn_message_received(self.api_on_message)
        self.api_thread = Thread(target=self.api.run_forever)
        self.api_thread.start()
        self.logger.info('Swarm API server started, listening on {}:{}'.format(self.host, self.api_port))
        self.report_queue = queue.Queue()
        self.reports_thread = Thread(target=self.reports_listener)
        self.reports_thread.start()
        self.cartography = {'messages': {}}

    def api_on_message(self, client, server, message):
        self.logger.info('Recieved from {}: {}'.format(client['address'], message))
        message = ast.literal_eval(message)
        if 'id' not in message.keys():
            message['id'] = str(uuid.uuid4())
        self.cartography['messages'][message['id']] = client
        if message['bot']['id'] not in self.cartography.keys():
            self.logger.info('Bot is not running. Starting commander for {}'.format(message['bot']['name']))
            self.spawn_commander(json.loads(json.dumps(message['bot'])))
        self.logger.info('Adding strategy {} to {}'.format(message, message['bot']['name']))
        self.cartography[message['bot']['id']]['strategies_queue'].put(message)

    def reports_listener(self):
        while 1:
            report = self.report_queue.get()
            self.logger.info('New report: {}'.format(report))
            print(self.cartography)
            client = self.cartography['messages'].pop(report['id'])
            self.api.send_message(client, str(report))

    def spawn_commander(self, bot: dict):
        self.cartography[bot['id']] = bot
        self.cartography[bot['id']].update({'strategies_queue': queue.Queue()})
        self.cartography[bot['id']].update({'thread': Thread(target=Commander, args=(bot, self.cartography[bot['id']]['strategies_queue'], self.report_queue))})
        self.cartography[bot['id']]['thread'].start()


if __name__ == '__main__':
    swarm_node = SwarmNode('localhost')
    # swarm_node.spawn_commander(bot={'id': 0, 'name': 'Ilancelet', 'username': '?', 'password': '?', 'server': 'Julith'})
    time.sleep(5)
