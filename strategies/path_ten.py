import json
import time

import strategies
from strategies import support_functions, goto
from tools import logger as log


def path_ten(**kwargs):
    """
    Walks around to get to level ten by earning successes

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()
    if listener.game_state['level'] >= 10:
        logger.info('Bot is already at least level 10')
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': time.time() - global_start}
        }
        log.close_logger(logger)
        return strategy

    path = [
        {'pos': [-2, -4], 'worldmap': 2},
        {'pos': [-2, -2], 'worldmap': 2},
        {'pos': [1, -2], 'worldmap': 2},
        {'pos': [1, -4], 'worldmap': 2},
        {'pos': [2, -14]},
        {'pos': [3, -14]},
        {'pos': [8, -15]},
        {'pos': [9, -25]},
        {'pos': [3, -32]},
        {'pos': [2, -27]},
        {'pos': [-3, -28]},
        {'pos': [-6, -29]},
        {'pos': [-5, -36]},
        {'pos': [-5, -47]},
        {'pos': [-8, -54]},
        {'pos': [-9, -54]},
        {'pos': [-15, -54]},
        {'pos': [-19, -56]},
        {'pos': [-19, -57]},
        {'pos': [-24, -62]},
        {'pos': [-28, -63]},
        {'pos': [-29, -60]},
        {'pos': [-27, -59]},
        {'pos': [-27, -55]},
        {'pos': [-27, -51]},
        {'pos': [-29, -53]},
        {'pos': [-30, -58]},
        {'pos': [-34, -53]},
        {'pos': [-34, -52]},
        {'pos': [-35, -52]},
        {'pos': [-35, -54]},
        {'pos': [-34, -59]},
    ]
    for pos in path:
        sub_strategy = strategies.goto.goto(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    'x': pos['pos'][0],
                    'y': pos['pos'][1],
                    'worldmap': pos['worldmap'] if 'worldmap' in pos.keys() else 1
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

        sub_strategy = strategies.achievement_reward.achievement_reward(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot']
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

    logger.info('Finished walking path 10 in {}s'.format(time.time() - global_start))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy