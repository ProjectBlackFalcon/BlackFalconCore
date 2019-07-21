import json
import time

from tools import logger as log
import strategies


def bank_close(**kwargs):
    """
    A strategy to close a bank

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    if not listener.game_state['storage_open']:
        logger.info('Closed bank in {}s'.format(0))
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': 0}
        }
        log.close_logger(logger)
        return strategy

    # Open NPC
    order = {
        'command': 'close_npc',
        'parameters': {}
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if not listener.game_state['storage_open']:
            waiting = False
        time.sleep(0.05)

    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed to close bank {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed to close bank {}s'.format(execution_time)}
        }
        log.close_logger(logger)
        return strategy

    execution_time = time.time() - global_start
    logger.info('Closed bank in {}s'.format(execution_time))
    strategy['report'] = {
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy