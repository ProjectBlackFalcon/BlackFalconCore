import json

import time

from tools import logger as log
from strategies import goto, auctionh_get_prices


def auctionh_get_all_prices(**kwargs):
    """
    A strategy to get all the prices from the auction houses

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()
    n_new_entries = 0

    path = [
        (6, -17),
        (4, -17),
        (3, -19),
    ]
    if listener.game_state['sub_end'] != 0 and listener.game_state['sub_end'] / 1000 - time.time() > 60 * 60 * 2:
        # TODO: Check that the sub time left is actually in seconds
        path = [
            (-30, -60),
            (-30, -53),
            (-27, -51),
            (-32, -55),
            (-36, -56)
        ]

    sample_timestamp = int(time.time())
    for pos in path:
        sub_strategy = goto.goto(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    'x': pos[0],
                    'y': pos[1]
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

        sub_strategy = auctionh_get_prices.auctionh_get_prices(
            assets=assets,
            orders_queue=orders_queue,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    "general_ids_list": 'all',
                    "sample_timestamp": sample_timestamp
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

        n_new_entries += sub_strategy['report']['details']['Number of new entries']

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start, 'Number of new entries': n_new_entries}
    }
    log.close_logger(logger)
    return strategy