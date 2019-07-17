import json
import time

from tools import logger as log
import strategies


def get_game_state(**kwargs):
    """
    A strategy to display a bot's game state.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start = time.time()
    game_state = listener.game_state
    execution_time = time.time() - start
    logger.info(
        'Fetched game state in {}s'.format(execution_time))

    pos = game_state['pos'] if 'pos' in game_state else [-100, -100]
    worldmap = game_state['worldmap'] if 'worldmap' in game_state else -100
    cell = game_state['cell'] if 'cell' in game_state else -100
    misc_stat = game_state['jobs'] if 'jobs' in game_state.keys() else None

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time, 'game_state': (pos, worldmap, cell, misc_stat)}
    }
    log.close_logger(logger)
    return strategy