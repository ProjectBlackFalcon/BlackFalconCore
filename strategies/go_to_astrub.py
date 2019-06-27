import json
import time

from tools import logger as log
import strategies


def go_to_astrub(**kwargs):
    """
    A strategy to go from Incarnam to Astrub trough the portal

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    order = {
        'command': 'open_npc',
        'parameters': {
            'map_id': listener.game_state['map_id'],
            'npc_id': -20000,
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if listener.game_state['npc_dialog_open']:
            waiting = False
        time.sleep(0.05)

    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed going through the portal from Incarnam to Astrub in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    order = {
        'command': 'answer_npc',
        'parameters': {
            'reply_id': 36982
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['pos'] == [6, -19]:
                waiting = False
        time.sleep(0.05)

    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed going through the portal from Incarnam to Astrub in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    report = strategies.change_map(
        listener=listener,
        strategy={
            'bot': strategy['bot'],
            'parameters': {
                'cell': 508,
                'direction': 'w'
            }
        },
        orders_queue=orders_queue
    )
    execution_time = time.time() - global_start
    if not report['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Exiting portal room failed'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Went from Incarnam to Astrub in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy