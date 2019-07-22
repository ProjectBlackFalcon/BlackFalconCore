import json
import os
import queue
import time
import uuid
from multiprocessing import cpu_count
from multiprocessing.pool import Pool
from threading import Thread

from websocket_server import WebsocketServer

import strategies
from strategies import support_functions
from strategies import *
from client.commander import Commander
from tools import logger
import assets_downloader


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
        assets_downloader.update_assets()
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
            if len(file_pack) <= 4:
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
            else:
                with Pool(cpu_count() - 1) as p:
                    results_list = p.map(self.load_asset_chunk, [assets_paths + '/' + file_name for file_name in file_pack])
                for asset_chunk in results_list:
                    if asset_name not in self.assets.keys():
                        self.assets[asset_name] = asset_chunk
                    else:
                        if type(asset_chunk) is list:
                            self.assets[asset_name] += asset_chunk
                        elif type(asset_chunk) is dict:
                            self.assets[asset_name].update(asset_chunk)
        self.logger.info('Done loading assets in {}s'.format(round(time.time() - start, 2)))

    def load_asset_chunk(self, file_path):
        with open(file_path, 'r', encoding='utf8') as f:
            chunk = json.load(f)
        return chunk

    def api_on_message(self, client, server, message):
        self.logger.info('Recieved from {}: {}'.format(client['address'], message))
        message = json.loads(message)
        if 'id' not in message.keys():
            message['id'] = str(uuid.uuid4())
        self.cartography['messages'][message['id']] = client
        intercept_command = False

        if message['command'] == 'new_bot':
            intercept_command = True
            self.logger.info('Creating new bot : ' + str(message['parameters']))
            try:
                strategies.support_functions.create_profile(
                    id=message['parameters']['id'],
                    bot_name=message['bot'],
                    password=message['parameters']['password'],
                    username=message['parameters']['username'],
                    server=message['parameters']['server']
                )
                self.logger.info('Created : ' + str(message['bot']))
                message['success'] = True
                message['details'] = {}
                self.api.send_message(client, json.dumps(message))
            except Exception as e:
                if e.args[0] == 'Bot already exists. Delete it using the \'delete_bot\' command first.':
                    self.logger.warn('Failed creating : ' + str(message['bot']))
                    message['success'] = False
                    message['details'] = {'reason': e.args[0]}
                    self.api.send_message(client, json.dumps(message))
                else:
                    raise
                return

        if message['command'] == 'delete_bot':
            strategies.support_functions.delete_profile(message['bot'])
            message['success'] = True
            message['details'] = {}
            if message['bot'] in self.cartography.keys():
                # TODO: This is shit, implement a kill commander order or something.
                del self.cartography[message['bot']]
            self.api.send_message(client, json.dumps(message))
            return

        if message['bot'] not in self.cartography.keys():
            self.logger.info('Bot is not running. Starting commander for {}'.format(message['bot']))
            try:
                self.spawn_commander(json.loads(json.dumps(message['bot'])), client)
            except Exception as e:
                if e.args[0] == 'Bot does not exist. Create a profile using the \'new_bot\' command first.':
                    message['success'] = False
                    message['details'] = {'reason': e.args[0]}
                    self.api.send_message(client, json.dumps(message))
                else:
                    raise
                return

        if not intercept_command:
            self.logger.info('Adding strategy to {}: {}'.format(message['bot'], message))
            self.cartography[message['bot']]['strategies_queue'].put(message)

    def reports_listener(self):
        while 1:
            report = self.report_queue.get()
            if 'exception_notif' in report.keys():
                # A component of a bot died, kill the rest of it
                client = self.cartography[report['bot']]['client']
                self.kill_commander(report['bot'])
            else:
                # Business as usual
                client = self.cartography['messages'].pop(report['id'])

            self.api.send_message(client, json.dumps(report))
            self.logger.info('New report from {}: {}'.format(report['bot'], report))

    def spawn_commander(self, bot_name, client):
        if bot_name in self.cartography.keys():
            raise Exception('{} is already used elsewhere'.format(bot_name))
        bot_profile = strategies.support_functions.get_profile(bot_name)
        self.cartography[bot_name] = {}
        self.cartography[bot_name].update({'strategies_queue': queue.Queue()})
        self.cartography[bot_name].update({'thread': Thread(target=Commander, args=(bot_profile, self.cartography[bot_name]['strategies_queue'], self.report_queue, self.assets))})
        self.cartography[bot_name]['thread'].start()
        self.cartography[bot_name]['client'] = client

    def kill_commander(self, bot_name):
        self.cartography[bot_name]['strategies_queue'].put({'stop': 'die'})
        del self.cartography[bot_name]


if __name__ == '__main__':
    swarm_node = SwarmNode(host='0.0.0.0')
    # swarm_node.spawn_commander(bot={'id': 0, 'name': 'Ilancelet', 'username': '?', 'password': '?', 'server': 'Julith'})
    time.sleep(5)
