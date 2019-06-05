import json
import time

from tools import logger as log


def connect(**kwargs):
    """
    A strategy to connect a bot.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot']['name'])

    if 'connected' in listener.game_state.keys():
        if listener.game_state['connected']:
            logger.info('Bot connected in {}s'.format(0))
            strategy['report'] = {
                'success': True,
                'details': {'Execution time': 0}
            }
            return strategy

    order = {
        'command': strategy['command'],
        'parameters': {
            'username': strategy['bot']['username'],
            'password': strategy['bot']['password'],
            'server': strategy['bot']['server'],
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 20 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'connected' in listener.game_state.keys():
            if listener.game_state['connected']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed connecting in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        return strategy

    logger.info('Connected {} in {}s'.format(strategy['bot']['name'], execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
