import json
import time

from tools import logger as log
import strategies


def auctionh_close(**kwargs):
    """
    A strategy to close the auction house.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    if not listener.game_state['auction_house_info']:
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': time.time() - global_start}
        }
        log.close_logger(logger)
        return strategy

    order = {
        "command": "close_npc"
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'auction_house_info' in listener.game_state.keys():
            if not listener.game_state['auction_house_info']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed closing the auction house in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed closing the auction house in {}s'.format(execution_time)}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Closed the auction house in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy