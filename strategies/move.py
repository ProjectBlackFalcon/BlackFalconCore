import json
import time

import strategies
from tools import logger as log


def move(**kwargs):
    """
    A strategy move the bot within a map.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    if 'cell' in listener.game_state.keys():
        if listener.game_state['cell'] == strategy['parameters']['cell']:
            logger.info('Completed move to cell {} in {}s'.format(strategy['parameters']['cell'], 0))
            strategy['report'] = {
                'success': True,
                'details': {'Execution time': 0}
            }
            log.close_logger(logger)
            return strategy

    current_pos = '{};{}'.format(listener.game_state['pos'][0], listener.game_state['pos'][1])
    map_data = strategies.support_functions.fetch_map(assets['map_info'], current_pos, listener.game_state['worldmap'])
    order = {
        'command': 'move',
        'parameters': {
            "isUsingNewMovementSystem": map_data['isUsingNewMovementSystem'],
            "cells": map_data['rawCells'],
            "target_cell": strategy['parameters']['cell']
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 20 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if listener.game_state['cell'] == strategy['parameters']['cell']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed moving to cell {} in {}s'.format(strategy['parameters']['cell'], execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Completed move to cell {} in {}s'.format(strategy['parameters']['cell'], execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
