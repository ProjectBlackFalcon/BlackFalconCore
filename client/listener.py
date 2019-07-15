import time
from queue import Queue
from tools import logger
import json
from strategies import support_functions


class Listener:
    def __init__(self, bot: dict, assets):
        """
        The listener receives the data stream coming from the game trough the API. It maintains the current game state and a read only copy that the commander may access.

        :param bot: the bot dict.
        """
        self.assets = assets
        self.logger = logger.get_logger(__name__, bot['name'])
        self.output_queue = Queue()
        self._game_state = {
            'name': bot['name'],
            'id': bot['id'],
            'username': bot['username'],
            'password': bot['password'],
            'server': bot['server'],
            'npc_dialog_open': False,
            'npc_current_question': None,
            'npc_possible_replies': None,
            'zaap_dialog_open': False,
            'zaap_destinations': None,
            'in_fight': False
        }
        self.game_state = json.loads(json.dumps(self._game_state))
        self.messages_queue = []

    def run(self):
        self.logger.info('Starting listening for game state changes')
        while 1:
            data = json.loads(self.output_queue.get()[0])
            # self.logger.info('Listener received {}'.format(data))
            self.messages_queue.append((time.time(), data))
            self.messages_queue = self.messages_queue[1:] if len(self.messages_queue) > 100 else self.messages_queue
            self.update_game_state(data)
            self.game_state = json.loads(json.dumps(self._game_state))

    def update_game_state(self, data):
        if data['message'] == 'InventoryContentMessage':
            self._game_state['kamas'] = data['content']['kamas']
            self._game_state['inventory'] = data['content']['objects']  # TODO: formatting

        # if data['message'] == 'KamasUpdateMessage':
        #     self._game_state['kamas'] = data['content']['kamas']

        if data['message'] == 'CharacterSelectedSuccessMessage':
            self._game_state['level'] = data['content']['infos']['level']
            self._game_state['actor_id'] = data['content']['infos']['id']

        if data['message'] == 'CharacterLevelUpMessage':
            self._game_state['level'] += 1

        if data['message'] == 'InventoryWeightMessage':
            self._game_state['weight'] = data['content']['inventoryWeight']
            self._game_state['max_weight'] = data['content']['weightMax']

        if data['message'] == 'CharacterLoadingCompleteMessage':
            self._game_state['connected'] = True

        if data['message'] in ['MapComplementaryInformationsDataMessage', 'MapComplementaryInformationsDataInHavenBagMessage']:
            if data['message'] == 'MapComplementaryInformationsDataInHavenBagMessage':
                self._game_state['in_haven_bag'] = True
            else:
                self._game_state['in_haven_bag'] = False
            self._game_state['map_id'] = int(data['content']['mapId'])
            self._game_state['pos'] = support_functions.map_id_2_coord(self.assets['map_info'], self._game_state['map_id'])
            for actor in data['content']['actors']:
                if 'name' in actor.keys() and actor['name'] == self._game_state['name']:
                    self._game_state['cell'] = actor['disposition']['cellId']

            self._game_state['worldmap'] = support_functions.get_worldmap(self.assets['map_info'], self._game_state['map_id'])
            self._game_state['map_mobs'] = []
            self._game_state['map_npc'] = []
            self._game_state['map_players'] = []
            self._game_state['map_elements'] = []
            for actor in data['content']['actors']:
                if actor['contextualId'] < 0:
                    if 'npcId' in actor.keys():
                        self._game_state['map_npc'].append(actor)
                    if 'staticInfos' in actor.keys():
                        self._game_state['map_mobs'].append(actor)
                else:
                    self._game_state['map_players'].append(actor)
            if 'interactiveElements' in data['content'].keys():
                for element in data['content']['interactiveElements']:
                    if element['onCurrentMap']:
                        self._game_state['map_elements'].append(element)

        if data['message'] == 'GameMapMovementMessage':
            if data['content']['actorId'] == self._game_state['actor_id']:
                self._game_state['cell'] = data['content']['keyMovements'][-1]
                self._game_state['currently_walking'] = True

        if data['message'] == 'GameMapMovementConfirmMessage':
            self._game_state['currently_walking'] = False

        if data['message'] == 'NpcDialogQuestionMessage':
            self._game_state['npc_dialog_open'] = True
            self._game_state['npc_current_question'] = data['content']['messageId']
            self._game_state['npc_possible_replies'] = data['content']['visibleReplies']

        if data['message'] == 'ZaapDestinationsMessage':
            self._game_state['zaap_dialog_open'] = True
            self._game_state['zaap_destinations'] = data['content']['destinations']

        if data['message'] == 'LeaveDialogMessage':
            self._game_state['zaap_dialog_open'] = False
            self._game_state['zaap_destinations'] = None
            self._game_state['npc_dialog_open'] = False
            self._game_state['npc_current_question'] = None
            self._game_state['npc_possible_replies'] = None

        if data['message'] == 'GameFightStartingMessage':
            self._game_state['in_fight'] = True

        if data['message'] == 'ChallengeResultMessage':
            self._game_state['in_fight'] = False

    def received_message(self, start_time, message_id):
        for message in self.messages_queue:
            if start_time < message[0] and message_id == message[1]['id']:
                return True
        return False
