import json
import time

import strategies
from strategies import support_functions
from tools import logger as log


def use_zaap(**kwargs):
    """
    Uses a zaap to get to a specified destination
    The bot must be on a map with a zaap
    This strategy will move the bot to an appropriate cell to use the zaap

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    # TODO: Check that the map has a zaap

    # Move the bot the appropriate cell to activate the zaap
    zaap_cell, element_id, skill_uid = None, None, None
    current_cell = listener.game_state['cell']
    current_map = listener.game_state['pos']
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            if 'skillId' in element['enabledSkills'].keys() and element['enabledSkills']['skillId'] == 114:
                element_id = element['elementId']
                zaap_cell = assets['elements_info'][str(listener.game_state['map_id'])][element_id]
                skill_uid = element['enabledSkills']['skillInstanceUid']

    if zaap_cell is None and element_id is not None and skill_uid is not None:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Could not find a Zaap at {}, map id : {}'.format(current_map, listener.game_state['map_id'])}
        }

    zaap_use_cell = strategies.support_functions.get_closest_walkable_neighbour_cell(assets['map_info'], zaap_cell, current_cell, current_map, current_cell)
    report = strategies.move.move(
        listener=listener,
        strategy={'bot': strategy['bot'], 'parameters': {'cell': zaap_use_cell}},
        orders_queue=orders_queue
    )
    if not report['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Move to get to zaap failed'}
        }

    # TODO: Activate the zaap
    # TODO: Check that the bot has sufficient funds
    # TODO: Check that the bot knows the destination's zaap
    # TODO: Use it to go to destination

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
        if listener.game_state['zaap_dialog_open']:
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to open zaap menu in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout when opening zaap menu'}
        }
        return strategy

    logger.info('Opened zaap menu in {}s'.format(execution_time))

    # TODO: Check if the bot has enough money for the travel
    # TODO: Check if the target zaap is in the list of zaaps it can get to
    # TODO: Select a zaap from the list of possible destinations
    selected_zaap = None
    bot_strategy = {
        'command': 'travel_by_zaap',
        'parameters': {
            'target_map_id': selected_zaap
        }
    }
    logger.info('Sending order to bot API: {}'.format(json.dumps(bot_strategy)))
    orders_queue.put((json.dumps(bot_strategy),))

    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['pos'] == strategy['parameters']['target_zaap'] and listener.game_state['worldmap'] == 1:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to use zaap in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout when using zaap'}
        }
        return strategy

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }

    log.close_logger(logger)
    return strategy