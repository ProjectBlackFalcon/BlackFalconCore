import time
import uuid
from queue import Queue
from threading import Thread

from tools import logger
import json
from strategies import support_functions


class Listener:
    def __init__(self, bot: dict, assets):
        """
        The listener receives the data stream coming from the game trough the API. It maintains the current game state and a read only copy that the commander may access.

        :param bot: the bot dict.
        """
        self.stop = False
        self.assets = assets
        self.logger = logger.get_logger(__name__, bot['name'])
        self.output_queue = Queue()
        self.default_game_state = {
            'name': bot['name'],
            'id': bot['id'],
            'username': bot['username'],
            'password': bot['password'],
            'server': bot['server'],
            'connected': False,
            'sub_end': 0,
            'api_outdated': False,
            'banned': False,
            'npc_dialog_open': False,
            'npc_current_question': None,
            'npc_possible_replies': None,
            'zaap_dialog_open': False,
            'zaap_destinations': None,
            'in_fight': False,
            'storage_open': False,
            'jobs': {},
            'harvest_done': False,
            'harvest_started': False,
            'map_players': [],
            'map_elements': [],
            'stated_elements': [],
            'file_request_message': {'timestamp': 0},
            'auction_house_info': [],
            'achievement_available': []
        }
        self._game_state = json.loads(json.dumps(self.default_game_state))
        self.game_state = json.loads(json.dumps(self._game_state))
        self.messages_queue = []

    def run(self):
        self.logger.info('Starting listening for game state changes')
        while not self.stop:
            data = json.loads(self.output_queue.get()[0])
            # self.logger.info('Listener received {}'.format(data))
            self.messages_queue.append((time.time(), data))
            self.messages_queue = self.messages_queue[1:] if len(self.messages_queue) > 100 else self.messages_queue
            self.update_game_state(data)
            self.game_state = json.loads(json.dumps(self._game_state))
        self.logger.info('Listener shut down')
        logger.close_logger(self.logger)

    def update_game_state(self, data):
        if 'message' in data.keys():
            if data['message'] == 'IdentificationSuccessMessage':
                self._game_state['sub_end'] = data['content']['subscriptionEndDate']

            if data['message'] in ['JobExperienceMultiUpdateMessage', 'JobExperienceUpdateMessage']:
                if data['message'] == 'JobExperienceMultiUpdateMessage':
                    jobs_dict = {str(job['jobId']): job for job in data['content']['experiencesUpdate']}
                elif data['message'] == 'JobExperienceUpdateMessage':
                    jobs_dict = {str(data['content']['experiencesUpdate']['jobId']): data['content']['experiencesUpdate']}

                for key, value in jobs_dict.items():
                    if key in self._game_state['jobs'].keys():
                        self._game_state['jobs'][key].update(value)
                    else:
                        self._game_state['jobs'][key] = value

            if data['message'] == 'JobDescriptionMessage':
                for desc in data['content']['jobsDescription']:
                    if str(desc['jobId']) in self._game_state['jobs'].keys():
                        self._game_state['jobs'][str(desc['jobId'])]['skills'] = desc['skills']
                    else:
                        self._game_state['jobs'][str(desc['jobId'])] = {'skills': desc['skills']}

            if data['message'] == 'JobLevelUpMessage':
                self._game_state['jobs'][str(data['content']['jobsDescription']['jobId'])]['level'] = data['content']['newLevel']
                self._game_state['jobs'][str(data['content']['jobsDescription']['jobId'])]['skills'] = data['content']['jobsDescription']['skills']

            if data['message'] == 'InventoryContentMessage':
                self._game_state['kamas'] = data['content']['kamas']
                self._game_state['inventory'] = data['content']['objects']

            if data['message'] == 'InventoryWeightMessage':
                self._game_state['weight'] = data['content']['inventoryWeight']
                if data['content']['weightMax'] != 0:
                    self._game_state['max_weight'] = data['content']['weightMax']

            if data['message'] == 'KamasUpdateMessage':
                self._game_state['kamas'] = data['content']['kamasTotal']

            if data['message'] == 'StorageKamasUpdateMessage':
                self._game_state['storage_content']['kamas'] = data['content']['kamasTotal']

            if data['message'] == 'CharacterSelectedSuccessMessage':
                self._game_state['level'] = data['content']['infos']['level']
                self._game_state['actor_id'] = data['content']['infos']['id']

            if data['message'] == 'CharacterLevelUpMessage':
                self._game_state['level'] += 1

            if data['message'] == 'CharacterLoadingCompleteMessage':
                self._game_state['connected'] = True
                Thread(target=support_functions.update_profile, args=(self._game_state['name'], 'connected', True)).start()

            if data['message'] == 'SystemMessageDisplayMessage':
                if 'content' in data.keys() and 'hangUp' in data['content'].keys() and data['content']['hangUp']:
                    self._game_state = json.loads(json.dumps(self.default_game_state))

            if data['message'] == 'IdentificationFailedForBadVersionMessage':
                self._game_state['api_outdated'] = True

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
                self._game_state['stated_elements'] = []
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
                if 'statedElements' in data['content'].keys():
                    for element in data['content']['statedElements']:
                        if element['onCurrentMap']:
                            self._game_state['stated_elements'].append(element)

                # Update positions in Mongo profile
                pos = json.loads(json.dumps(tuple(self._game_state['pos'])))
                Thread(target=support_functions.update_profile, args=(self._game_state['name'], 'position', pos)).start()
                cell = self._game_state['cell']
                Thread(target=support_functions.update_profile, args=(self._game_state['name'], 'cell', cell)).start()
                worldmap = self._game_state['worldmap']
                Thread(target=support_functions.update_profile, args=(self._game_state['name'], 'worldmap', worldmap)).start()

            if data['message'] == 'StatedElementUpdatedMessage':
                for element in self._game_state['stated_elements']:
                    if element['elementId'] == data['content']['statedElement']['elementId']:
                        element['elementId'] = data['content']['statedElement']
                        break

            if data['message'] == 'InteractiveElementUpdatedMessage':
                for element in self._game_state['map_elements']:
                    if element['elementId'] == data['content']['interactiveElement']['elementId']:
                        element['elementId'] = data['content']['interactiveElement']
                        break

            if data['message'] == 'GameMapMovementMessage':
                if data['content']['actorId'] == self._game_state['actor_id']:
                    self._game_state['cell'] = data['content']['keyMovements'][-1]
                    self._game_state['currently_walking'] = True
                    Thread(target=support_functions.update_profile, args=(self._game_state['name'], 'cell', self._game_state['cell'])).start()

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

            if data['message'] == 'StorageInventoryContentMessage':
                self._game_state['storage_open'] = True
                self._game_state['storage_content'] = data['content']

            if data['message'] == 'ExchangeLeaveMessage':
                self._game_state['storage_open'] = False
                self._game_state['storage_content'] = []
                self._game_state['auction_house_info'] = []

            if data['message'] == 'InteractiveUsedMessage':
                self._game_state['harvest_started'] = True
                self._game_state['harvest_done'] = False

            if data['message'] == 'InteractiveUseEndedMessage':
                self._game_state['harvest_started'] = False
                self._game_state['harvest_done'] = True

            if data['message'] == 'CheckFileRequestMessage':
                self._game_state['file_request_message'] = {
                    'timestamp': time.time(),
                    'filename': data['content']['filename'],
                    'type': data['content']['type']
                }

            if data['message'] == 'ObjectQuantityMessage':
                for item in self._game_state['inventory']:
                    if item['objectUID'] == data['content']['objectUID']:
                        item['quantity'] = data['content']['quantity']

            if data['message'] == 'ObjectsQuantityMessage':
                for new_item in data['content']['objectsUIDAndQty']:
                    for item in self._game_state['inventory']:
                        if item['objectUID'] == new_item['objectUID']:
                            item['quantity'] = new_item['quantity']

            if data['message'] == 'ObjectDeletedMessage':
                for index, item in enumerate(self._game_state['inventory']):
                    if item['objectUID'] == data['content']['objectUID']:
                        del self._game_state['inventory'][index]
                        break

            if data['message'] == 'ObjectsDeletedMessage':
                for uid in data['content']['objectUID']:
                    for index, item in enumerate(self._game_state['inventory']):
                        if item['objectUID'] == uid:
                            del self._game_state['inventory'][index]
                            break

            if data['message'] == 'ObjectAddedMessage':
                self._game_state['inventory'].append(data['content']['object'])

            if data['message'] == 'ObjectsAddedMessage':
                self._game_state['inventory'] += data['content']['object']

            if data['message'] == 'StorageObjectUpdateMessage':
                for item in self._game_state['storage_content']['objects']:
                    if item['objectUID'] == data['content']['object']['objectUID']:
                        item['quantity'] = data['content']['object']['quantity']

            if data['message'] == 'StorageObjectsUpdateMessage':
                for new_item in data['content']['objectList']:
                    found = False
                    for index, item in enumerate(self._game_state['storage_content']['objects']):
                        if item['objectUID'] == new_item['objectUID']:
                            found = True
                            self._game_state['storage_content']['objects'][index] = new_item
                            break
                    if not found:
                        self._game_state['storage_content']['objects'].append(new_item)

            if data['message'] == 'StorageObjectRemoveMessage':
                for index, item in enumerate(self._game_state['storage_content']['objects']):
                    if item['objectUID'] == data['content']['objectUID']:
                        del self._game_state['storage_content']['objects'][index]
                        break

            if data['message'] == 'StorageObjectsRemoveMessage':
                for uid in data['content']['objectUIDList']:
                    for index, item in enumerate(self._game_state['storage_content']['objects']):
                        if item['objectUID'] == uid:
                            del self._game_state['storage_content']['objects'][index]
                            break

            if data['message'] == 'ExchangeStartedBidBuyerMessage':
                self._game_state['auction_house_info'] = data['content']  # What the player can buy
                self._game_state['auction_house_mode'] = 'buy'

            if data['message'] == 'ExchangeStartedBidSellerMessage':
                self._game_state['auction_house_info'] = data['content']  # What the player can sell
                self._game_state['auction_house_mode'] = 'sell'

            if data['message'] == 'ExchangeTypesExchangerDescriptionForUserMessage':
                if not len(data['content']['typeDescription']):
                    self._game_state['auction_house_info']['items_available'] = [str(uuid.uuid4())]
                else:
                    self._game_state['auction_house_info']['items_available'] = data['content']['typeDescription']

            if data['message'] == 'ExchangeTypesItemsExchangerDescriptionForUserMessage':
                # Used to properly register changes in item selection
                if 'item_selected' not in self._game_state['auction_house_info'].keys():
                    self._game_state['auction_house_info']['item_selected'] = [data['content']['itemTypeDescriptions']]

                elif len(self._game_state['auction_house_info']['item_selected']) < 2:
                    self._game_state['auction_house_info']['item_selected'].append(data['content']['itemTypeDescriptions'])

                elif data['content']['itemTypeDescriptions'] != self._game_state['auction_house_info']['item_selected'][0]:
                    del self._game_state['auction_house_info']['item_selected'][0]
                    self._game_state['auction_house_info']['item_selected'].append(data['content']['itemTypeDescriptions'])

                # Used to collect th items data
                self._game_state['auction_house_info']['actual_item_selected'] = data['content']['itemTypeDescriptions']

            # if data['message'] == 'ExchangeErrorMessage' and 'errorType' in data['content'].keys() and data['content']['errorType'] == 11:
            #     # Item is not for sale
            #     if 'item_selected' not in self._game_state['auction_house_info'].keys():
            #         self._game_state['auction_house_info']['item_selected'] = [str(uuid.uuid4())]
            #
            #     elif len(self._game_state['auction_house_info']['item_selected']) < 2:
            #         self._game_state['auction_house_info']['item_selected'].append(str(uuid.uuid4()))
            #
            #     else:
            #         del self._game_state['auction_house_info']['item_selected'][0]
            #         self._game_state['auction_house_info']['item_selected'].append(str(uuid.uuid4()))

            if data['message'] == 'AchievementFinishedMessage':
                self._game_state['achievement_available'].append(str(uuid.uuid4()))

            if data['message'] == 'AchievementRewardSuccessMessage':
                self._game_state['achievement_available'] = []

            if data['message'] == 'AccountLoggingKickedMessage':
                support_functions.update_profile(self.game_state['name'], 'banned', True)
                support_functions.update_account(self.game_state['username'], 'status', 'banned')
                self._game_state['banned'] = True
                self.stop = True

            if data['message'] == 'IdentificationFailedMessage':
                if 'reason' in data['content'].keys() and data['content']['reason'] == 3:
                    support_functions.update_profile(self.game_state['name'], 'banned', True)
                    support_functions.update_account(self.game_state['username'], 'status', 'banned')
                    self._game_state['banned'] = True
                    self.stop = True

            if data['message'] == 'IdentificationFailedBannedMessage':
                if 'reason' in data['content'].keys() and data['content']['reason'] == 3:
                    support_functions.update_profile(self.game_state['name'], 'banned', True)
                    support_functions.update_account(self.game_state['username'], 'status', 'banned')
                    self._game_state['banned'] = True
                    self.stop = True
