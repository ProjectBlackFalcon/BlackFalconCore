import queue
from threading import Thread

from client.commander import Commander
from tools import logger


class SwarmManager:
    def __init__(self):
        self.logger = logger.get_logger(__name__, 'swarm_manager')
        self.cartography = {}

    def spawn_commander(self, bot: dict):
        self.cartography[bot['id']] = bot
        self.cartography[bot['id']]['orders_queue'] = queue.Queue()
        self.cartography[bot['id']]['thread'] = Thread(Commander, args=(bot, self.cartography['orders_queue']))
        self.cartography[bot['id']]['thread'].start()