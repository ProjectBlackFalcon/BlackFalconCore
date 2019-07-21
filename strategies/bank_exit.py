import json
import time

from tools import logger as log
import strategies
from strategies import support_functions


def bank_exit(**kwargs):
    """
    A strategy to exit a bank

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    if listener.game_state['worldmap'] == 1:
        logger.info('Already outside bank in {}s'.format(0))
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': 0}
        }
        log.close_logger(logger)
        return strategy

    # Move the bot the appropriate cell to activate the map change
    map_change_cell, element_id = None, None
    current_cell = listener.game_state['cell']
    current_map = listener.game_state['pos']
    dist = 100000
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == 339:
                    tmp_element_id = element['elementId']
                    tmp_map_change_cell = assets['elements_info'][str(listener.game_state['map_id'])][str(tmp_element_id)]['cell']
                    if map_change_cell is None or strategies.support_functions.distance_cell(tmp_map_change_cell, current_cell) < dist:
                        dist = strategies.support_functions.distance_cell(tmp_map_change_cell, current_cell)
                        element_id = tmp_element_id
                        map_change_cell = tmp_map_change_cell

    if map_change_cell is None or element_id is None:
        strategy['report'] = {
            'success': False,
            'details': {
                'Execution time': time.time() - start,
                'Reason': 'Could not find a change map cell at {}, map id : {}'.format(current_map, listener.game_state['map_id'])
            }
        }
        log.close_logger(logger)
        return strategy

    order = {
        'command': 'move',
        'parameters': {
            "isUsingNewMovementSystem": False,
            "cells": [[True, False, 0, 0, True, 0] for _ in range(560)],
            "target_cell": map_change_cell
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'worldmap' in listener.game_state.keys():
            if listener.game_state['worldmap'] == 1:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed going to cell {} in {}s'.format(map_change_cell, execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed going to cell {} in {}s'.format(map_change_cell, execution_time)}
        }
        log.close_logger(logger)
        return strategy

    execution_time = time.time() - global_start
    logger.info('Exited building in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy