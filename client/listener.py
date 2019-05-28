from queue import Queue
from tools import logger
import json


class Listener:
    def __init__(self, bot: dict):
        """
        The listener receives the data stream coming from the game trough the API. It maintains the current game state and a read only copy that the commander may access.

        :param bot: the bot dict.
        """
        self.logger = logger.get_logger(__name__, bot['name'])
        self.output_queue = Queue()
        self._game_state = {
            'name': bot['name'],
            'id': bot['id'],
            'username': bot['username'],
            'password': bot['password'],
            'server': bot['server'],
        }
        self.game_state = json.loads(json.dumps(self._game_state))

    def listener(self):
        while 1:
            data = self.output_queue.get()
            self.update_game_state(data)
            self.game_state = json.loads(json.dumps(self._game_state))

    def update_game_state(self, data):
        pass
