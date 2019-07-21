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

    # Open NPC
    order = {
        'command': 'open_npc',
        'parameters': {
            'map_id': listener.game_state['map_id'],
            'npc_id': -20000,
            'action_id': 3
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
        logger.warning('Failed to open NPC dialog in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    # Answer first question
    order = {
        'command': 'answer_npc',
        'parameters': {
            'reply_id': listener.game_state['npc_possible_replies'][0]
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys():
            if listener.game_state['npc_current_question'] in [30639, 30638]:
                waiting = False
        time.sleep(0.05)

    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed answering first question in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    # Answer second question
    order = {
        'command': 'answer_npc',
        'parameters': {
            'reply_id': listener.game_state['npc_possible_replies'][0]
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
        logger.warning('Failed answering second question in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    # Go to cell 548
    order = {
        'command': 'move',
        'parameters': {
            "isUsingNewMovementSystem": False,
            "cells": [[True, False, 0, 0, True, 0] for _ in range(560)],
            "target_cell": 548
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['cell'] == 548:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start
    if waiting:
        logger.warning('Failed going to cell 548 in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    # Change map to 192416777
    order = {
        'command': 'change_map',
        'parameters': {
            'target_map_id': 192416777
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['map_id'] == 191106048:
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

    logger.info('Went from Incarnam to Astrub in {}s'.format(execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy