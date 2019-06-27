import json
import time

from tools import logger as log
import strategies


def go_to_incarnam(**kwargs):
    """
    A strategy to go from Astrub to Incarnam trough the portal

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    # Enter the portal room
    door_skill_id = 184
    element_id = 00000  # TODO Get from gamestate
    skill_uid = 00000  # TODO Get from gamestate
    order = {
        'command': 'use_interactive',
        'parameters': {
            'element_id': element_id,
            'skill_uid': skill_uid
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['worldmap'] == -1:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed entering the portal room in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Entered the portal room in {}s'.format(execution_time))

    # Use the portal
    # Check if Incarnam's portal is an interactive or an NPC ?
    door_skill_id = 184
    element_id = 00000  # TODO Get from gamestate
    skill_uid = 00000  # TODO Get from gamestate
    order = {
        'command': 'use_interactive',
        'parameters': {
            'element_id': element_id,
            'skill_uid': skill_uid
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['worldmap'] == 2:
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

    execution_time = time.time() - global_start
    logger.info('Went from Astrub to Incarnam in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
