import json
import time

from tools import logger as log
import strategies


def exit_bwork(**kwargs):
    """
    A strategy to exit bwork village.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    # Move the bot the appropriate cell to activate the door
    element_id, skill_uid = None, None
    current_map = listener.game_state['pos']
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == 184:
                    element_id = element['elementId']
                    skill_uid = skill['skillInstanceUid']

    if element_id is None or skill_uid is None:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start,
                        'Reason': 'Could not find a bwork door at {}, map id : {}'.format(current_map, listener.game_state['map_id'])}
        }
        log.close_logger(logger)
        return strategy

    report = strategies.move.move(
        strategy={
            'bot': strategy['bot'],
            'command': 'move',
            'parameters': {'cell': 260}
        },
        listener=listener,
        assets=assets,
        orders_queue=orders_queue
    )['report']

    if not report['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'reason': 'Move failed'}
        }
        log.close_logger(logger)
        return strategy

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
            if listener.game_state['pos'] == [-1, 8]:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed exiting bwork in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Exited bwork in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
