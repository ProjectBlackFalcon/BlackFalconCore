import queue
import time
from threading import Thread

from websocket_server import WebsocketServer

from client.commander import Commander
from tools import logger


class SwarmNode:
    def __init__(self, host):
        self.logger = logger.get_logger(__name__, 'swarm_manager')
        self.host = host
        self.api_port = 8721
        self.api = WebsocketServer(self.api_port, host=self.host)
        self.api.set_fn_message_received(self.api_on_message)
        self.api_thread = Thread(target=self.api.run_forever)
        self.api_thread.start()
        self.logger.info('Swarm API server started, listening on {}:{}'.format(self.host, self.api_port))

        self.cartography = {}

    def api_on_message(self, client, server, message):
        pass

    def spawn_commander(self, bot: dict):
        self.cartography[bot['id']] = bot
        print(self.cartography[bot['id']])
        self.cartography[bot['id']].update({'orders_queue': queue.Queue()})
        self.cartography[bot['id']].update({'thread': Thread(target=Commander, args=(bot, self.host, self.cartography[bot['id']]['orders_queue']))})
        self.cartography[bot['id']]['thread'].start()


if __name__ == '__main__':
    swarm_node = SwarmNode('localhost')
    swarm_node.spawn_commander(bot={'id': 0, 'name': 'Ilancelet', 'username': '?', 'password': '?', 'server': 'Julith'})
    time.sleep(5)
