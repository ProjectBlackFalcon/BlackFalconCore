import json
import time

import strategies
from strategies import support_functions, goto, harvest_map, go_drop_bank
from tools import logger as log


def harvest_duration(**kwargs):
    """
    Harvests the resources on a path of maps for a specific duration

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    path = strategy['parameters']['path']
    path_index = 0
    total_haul = {}
    while time.time() - global_start < 60 * strategy['parameters']['duration']:
        sub_strategy = strategies.goto.goto(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    'x': path[path_index]['pos'][0],
                    'y': path[path_index]['pos'][1],
                    'cell': path[path_index]['cell'] if 'cell' in path[path_index].keys() else None,
                    'worldmap': path[path_index]['worldmap'] if 'worldmap' in path[path_index].keys() else 1
                }
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

        sub_strategy = strategies.harvest_map.harvest_map(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    'whitelist': strategy['parameters']['whitelist'] if 'whitelist' in strategy['parameters'].keys() else None,
                    'blacklist': strategy['parameters']['blacklist'] if 'blacklist' in strategy['parameters'].keys() else None,
                }
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

        map_haul = sub_strategy['report']['details']['Collected']
        for item_name, haul in map_haul.items():
            if item_name in total_haul.keys():
                total_haul[item_name] += haul
            else:
                total_haul[item_name] = haul

        if listener.game_state['weight'] > listener.game_state['max_weight'] - 50:
            break
            sub_strategy = strategies.go_drop_bank.go_drop_bank(
                assets=assets,
                orders_queue=orders_queue,
                listener=listener,
                strategy={
                    'bot': strategy['bot'],
                    'parameters': {
                        'return': 'current'
                    }
                }
            )
            if not sub_strategy['report']['success']:
                strategy['report'] = {
                    'success': False,
                    'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
                }
                log.close_logger(logger)
                return strategy

        path_index = (path_index + 1) % (len(path) - 1)

    logger.info('Harvested for {}s. Total haul: {}'.format(time.time() - global_start, total_haul))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy