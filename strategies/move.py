import json
import time

from tools import logger as log


def move(**kwargs):
    """
    A strategy move the bot within a map.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot']['name'])

    if 'cell' in listener.game_state.keys():
        if listener.game_state['cell'] == strategy['parameters']['cell']:
            logger.info('Completed move to cell {} in {}s'.format(strategy['parameters']['cell'], 0))
            strategy['report'] = {
                'success': True,
                'details': {'Execution time': 0}
            }
            return strategy

    order = {
        'command': 'move',
        'parameters': strategy['parameters']
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 20 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['cell'] == strategy['parameters']['cell']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed moving to cell {} in {}s'.format(strategy['parameters']['cell'], execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        return strategy

    logger.info('Completed move to cell {} in {}s'.format(strategy['parameters']['cell'], execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
