import json
import time

from tools import logger as log
import strategies
from strategies import support_functions


def enter_bank(**kwargs):
    """
    A strategy to enter a bank

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    if listener.game_state['worldmap'] == -1:
        logger.info('Already inside bank (or at least underground) in {}s'.format(0))
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': 0}
        }
        log.close_logger(logger)
        return strategy

    # Move the bot the appropriate cell to activate the zaap
    door_cell, element_id, skill_uid = None, None, None
    current_cell = listener.game_state['cell']
    current_map = listener.game_state['pos']
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == 184:
                    element_id = element['elementId']
                    door_cell = assets['elements_info'][str(listener.game_state['map_id'])][str(element_id)]['cell']
                    skill_uid = skill['skillInstanceUid']

    if door_cell is None or element_id is None or skill_uid is None:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start,
                        'Reason': 'Could not find a Zaap at {}, map id : {}'.format(current_map, listener.game_state['map_id'])}
        }
        log.close_logger(logger)
        return strategy

    door_use_cell = strategies.support_functions.get_closest_walkable_neighbour_cell(assets['map_info'], door_cell, current_cell, current_map, listener.game_state['worldmap'])
    sub_strategy = strategies.move.move(
        listener=listener,
        strategy={'bot': strategy['bot'], 'parameters': {'cell': door_use_cell}},
        orders_queue=orders_queue,
        assets=assets
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Move to get to door failed'}
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
        if listener.game_state['worldmap'] == -1:
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to open bank door in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed to open bank door in {}s'.format(execution_time)}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Entered bank in {}s'.format(execution_time))

    execution_time = time.time() - global_start
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy