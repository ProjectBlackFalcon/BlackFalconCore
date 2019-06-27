import time
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
            'level': 0,
            'npc_dialog_open': False,
            'zaap_dialog_open': False
        }
        self.game_state = json.loads(json.dumps(self._game_state))
        self.messages_queue = []

    def run(self):
        self.logger.info('Starting listening for game state changes')
        while 1:
            data = self.output_queue.get()
            self.logger.info('Listener received {}'.format(data))
            self.messages_queue.append((time.time(), data))
            self.messages_queue = self.messages_queue[1:] if len(self.messages_queue) > 100 else self.messages_queue
            self.update_game_state(data)
            self.game_state = json.loads(json.dumps(self._game_state))

    def update_game_state(self, data):
        self.logger.info('Updating game state')
        # if data[0] == 'ping':
        #     self._game_state['ping'] = time.time()
        if data['id'] == 5617:
            self._game_state['npc_dialog_open'] = True
        if data['id'] == 6830:
            self._game_state['zaap_dialog_open'] = True
        if data['id'] == 5502:
            self._game_state['npc_dialog_open'] = False
            self._game_state['zaap_dialog_open'] = False

    def received_message(self, start_time, message_id):
        for message in self.messages_queue:
            if start_time < message[0] and message_id == message[1]['id']:
                return True
        return False
