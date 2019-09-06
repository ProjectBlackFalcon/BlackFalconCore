import ast
import json
import time

from strategies import support_functions, auctionh_close
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
    global_start = time.time()

    # Close the auction house if it is open
    if len(listener.game_state['auction_house_info']):
        sub_strategy = auctionh_close.auctionh_close(
            listener=listener,
            orders_queue=orders_queue,
            assets=assets,
            strategy={
                "bot": strategy['bot'],
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - global_start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

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
    map_data = support_functions.fetch_map(assets['map_info'], current_pos, listener.game_state['worldmap'])
    deserialized_raw_cells = []
    for cell in map_data['rawCells']:
        deserialized_raw_cells.append(ast.literal_eval(assets['map_info_index'][cell]))
    order = {
        'command': 'move',
        'parameters': {
            "isUsingNewMovementSystem": map_data['isUsingNewMovementSystem'],
            "cells": deserialized_raw_cells,
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
            'details': {'Execution time': execution_time, 'Reason': 'Timeout, no map movement for bot'}
        }
        log.close_logger(logger)
        return strategy

    start = time.time()
    timeout = 20 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'pos' in listener.game_state.keys() and 'worldmap' in listener.game_state.keys():
            if not listener.game_state['currently_walking']:
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed moving to cell {} in {}s'.format(strategy['parameters']['cell'], execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout, no movement confirmation'}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Completed move to cell {} in {}s'.format(strategy['parameters']['cell'], time.time() - global_start))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
