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

    logger = log.get_logger(__name__, strategy['bot']['name'])

    cell = strategy['parameters']['cell']
    direction = strategy['parameters']['direction']  # 'n', 's', 'w', 'e'

    global_start, start = time.time(), time.time()
    report = strategies.move(
        strategy={
            'bot': strategy['bot'],
            'command': 'move',
            'parameters': cell
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

    current_map = list(listener.game_state['pos'])
    target_map = [sum(term) for term in zip(current_map, [(0, -1), (0, 1), (-1, 0), (1, 0)][('n', 's', 'w', 'e').index(direction)])]
    order = {
        'command': strategy['command'],
        'parameters': strategy['parameters']['direction']
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['pos'] == target_map:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed changing map from {} to {} through cell {} in {}s'.format(current_map, target_map, cell, execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        return strategy

    logger.info('Changed map from {} to {} through cell {} in {}s'.format(current_map, target_map, cell, execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy