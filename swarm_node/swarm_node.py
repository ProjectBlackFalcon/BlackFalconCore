import ast
import json
import os
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
        self.assets = {}
        self.load_assets()
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

    def load_assets(self):
        start = time.time()
        assets_paths = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
        files_packs = {}
        self.logger.info('Mapping static assets')
        for file in os.listdir(assets_paths):
            if file.endswith('.json'):
                if file.replace('.json', '').split('_')[-1].isdigit():
                    if '_'.join(file.replace('.json', '').split('_')[:-1]) not in files_packs.keys():
                        files_packs['_'.join(file.replace('.json', '').split('_')[:-1])] = [file]
                    else:
                        files_packs['_'.join(file.replace('.json', '').split('_')[:-1])].append(file)
                else:
                    files_packs[file.replace('.json', '')] = [file]

        self.logger.info('Loading static assets...')
        for asset_name, file_pack in files_packs.items():
            self.logger.info('Loading asset: {}'.format(asset_name))
            for file in file_pack:
                with open(assets_paths + '/' + file, 'r', encoding='utf8') as f:
                    data = json.load(f)
                if asset_name not in self.assets.keys():
                    self.assets[asset_name] = data
                else:
                    if type(data) is list:
                        self.assets[asset_name] += data
                    elif type(data) is dict:
                        self.assets[asset_name].update(data)

        self.logger.info('Done loading assets in {}s'.format(round(time.time() - start, 2)))

    def api_on_message(self, client, server, message):
        self.logger.info('Recieved from {}: {}'.format(client['address'], message))
        message = ast.literal_eval(message)
        if 'id' not in message.keys():
            message['id'] = str(uuid.uuid4())
        self.cartography['messages'][message['id']] = client
        if message['bot']['id'] not in self.cartography.keys():
            self.logger.info('Bot is not running. Starting commander for {}'.format(message['bot']['name']))
            self.spawn_commander(json.loads(json.dumps(message['bot'])))
        self.logger.info('Adding strategy to {}: {}'.format(message['bot']['name'], message))
        self.cartography[message['bot']['id']]['strategies_queue'].put(message)

    def reports_listener(self):
        while 1:
            report = self.report_queue.get()
            self.logger.info('New report from {}: {}'.format(report['bot']['name'], report))
            client = self.cartography['messages'].pop(report['id'])
            self.api.send_message(client, str(report))

    def spawn_commander(self, bot: dict):
        self.cartography[bot['id']] = bot
        self.cartography[bot['id']].update({'strategies_queue': queue.Queue()})
        self.cartography[bot['id']].update({'thread': Thread(target=Commander, args=(bot, self.cartography[bot['id']]['strategies_queue'], self.report_queue, self.assets))})
        self.cartography[bot['id']]['thread'].start()


if __name__ == '__main__':
    swarm_node = SwarmNode(host='localhost')
    # swarm_node.spawn_commander(bot={'id': 0, 'name': 'Ilancelet', 'username': '?', 'password': '?', 'server': 'Julith'})
    time.sleep(5)
