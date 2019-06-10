import json
import time

from tools import logger as log
import strategies


def change_map(**kwargs):
    """
    A strategy make the bot move to an adjacent map.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()
    report = strategies.move(
        strategy={
            'bot': strategy['bot'],
            'command': 'move',
            'parameters': 110
        },
        listener=listener,
        orders_queue=orders_queue
    )['report']

    if not report['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'reason': 'Move failed'}
        }
        return strategy

    brak_door_id = 184
    order = {
        'command': 'use_interactive',
        'parameters': {'id': brak_door_id}
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['pos'] == (-25, 30):
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed exiting brak through the north gate in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        return strategy

    logger.info('Exited brak through the north gate in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
