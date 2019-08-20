import json
import time

from tools import logger as log


def achievement_reward(**kwargs):
    """
    A strategy to collect achievement rewards.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot'])

    if not len(listener.game_state['achievement_available']):
        logger.warn('No achievement available')
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': 0, 'Reason': 'No achievement available'}
        }
        log.close_logger(logger)
        return strategy

    order = {
        'command': 'achievement_get',
        'parameters': {
            'actor_id': listener.game_state['actor_id']
        }
    }
    achievements_list = listener.game_state['achievement_available'][:]
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if set(listener.game_state['achievement_available']) != set(achievements_list):
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to get achievement reward in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Got achievement reward in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
