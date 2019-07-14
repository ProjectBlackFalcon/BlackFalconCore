import json
import time

from tools import logger as log


def enter_havenbag(**kwargs):
    """
    A strategy to enter the haven bag.
    Checks if the player is level > 10 and if it's already inside.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot'])

    if listener.game_state['level'] < 10:
        logger.warn('Bot level too low')
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Bot level too low'}
        }
        log.close_logger(logger)
        return strategy

    if 'in_haven_bag' in listener.game_state.keys():
        if listener.game_state['in_haven_bag']:
            logger.info('Entered havenbag in {}s'.format(0))
            strategy['report'] = {
                'success': True,
                'details': {'Execution time': 0}
            }
            log.close_logger(logger)
            return strategy

    order = {
        'command': 'enter_havenbag'
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'in_haven_bag' in listener.game_state.keys():
            if listener.game_state['in_haven_bag']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed entering havenbag in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Entered havenbag in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy