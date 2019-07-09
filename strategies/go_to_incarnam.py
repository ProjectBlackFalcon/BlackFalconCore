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
    element_id, skill_uid = None, None
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == door_skill_id:
                    element_id = element['elementId']
                    skill_uid = skill['skillInstanceUid']

    if element_id is None or skill_uid is None:
        logger.warn('Failed entering the portal room in {}s'.format(0))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Could not find skill UID or element id'}
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
            if listener.game_state['map_id'] == 192416776:
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

    # Go to cell 468
    order = {
        'command': 'move',
        'parameters': {
            "isUsingNewMovementSystem": False,
            "cells": [[True, False, 0, 0, True, 0] for _ in range(560)],
            "target_cell": 468
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['cell'] == 468:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed going to cell 468 in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    # Use the portal
    door_skill_id = 184
    element_id, skill_uid = None, None
    for element in listener.game_state['map_elements']:
        if 'enabledSkills' in element.keys():
            for skill in element['enabledSkills']:
                if 'skillId' in skill.keys() and skill['skillId'] == door_skill_id:
                    element_id = element['elementId']
                    skill_uid = skill['skillInstanceUid']

    if element_id is None or skill_uid is None:
        logger.warn('Failed entering the portal room in {}s'.format(0))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Could not find skill UID or element id'}
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
