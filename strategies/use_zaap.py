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

    # Move the bot the appropriate cell to activate the zaap
    zaap_cell, element_id, skill_uid = None, None, None
    current_cell = listener.game_state['cell']
    current_map = listener.game_state['pos']
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == 114:
                    element_id = element['elementId']
                    zaap_cell = assets['elements_info'][str(listener.game_state['map_id'])][str(element_id)]['cell']
                    skill_uid = skill['skillInstanceUid']

    if zaap_cell is None or element_id is None or skill_uid is None:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Could not find a Zaap at {}, map id : {}'.format(current_map, listener.game_state['map_id'])}
        }
        log.close_logger(logger)
        return strategy

    if not listener.game_state['in_haven_bag']:
        zaap_use_cell = strategies.support_functions.get_closest_walkable_neighbour_cell(assets['map_info'], zaap_cell, current_cell, current_map, listener.game_state['worldmap'])
        sub_strategy = strategies.move.move(
            listener=listener,
            strategy={'bot': strategy['bot'], 'parameters': {'cell': zaap_use_cell}},
            orders_queue=orders_queue,
            assets=assets
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': 'Move to get to zaap failed'}
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
        log.close_logger(logger)
        return strategy

    logger.info('Opened zaap menu in {}s'.format(execution_time))

    target_map_id = int(strategies.support_functions.fetch_map(assets['map_info'], coord='{};{}'.format(strategy['parameters']['destination_x'], strategy['parameters']['destination_y']), worldmap=1)['id'])
    selected_destination = None
    for destination in listener.game_state['zaap_destinations']:
        if destination['mapId'] == target_map_id:
            selected_destination = destination

    if selected_destination is None:
        logger.warn('Zaap at destination [{},{}] is not known'.format(strategy['parameters']['destination_x'], strategy['parameters']['destination_y']))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Zaap at destination [{},{}] is not known'.format(strategy['parameters']['destination_x'], strategy['parameters']['destination_y'])}
        }
        log.close_logger(logger)
        return strategy

    if selected_destination['cost'] > listener.game_state['kamas']:
        logger.warn('Not enough money to use zaap: needed {}, available: {}'.format(selected_destination['cost'], listener.game_state['kamas']))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Not enough money to use zaap: needed {}, available: {}'.format(selected_destination['cost'], listener.game_state['kamas'])}
        }
        log.close_logger(logger)
        return strategy

    order = {
        'command': 'travel_by_zaap',
        'parameters': {
            'target_map_id': selected_destination['mapId']
        }
    }
    logger.info('Sending order to bot API: {}'.format(json.dumps(order)))
    orders_queue.put((json.dumps(order),))

    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['map_id'] == selected_destination['mapId']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to use zaap in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Teleport by zaap failed'}
        }
        log.close_logger(logger)
        return strategy

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }

    log.close_logger(logger)
    return strategy