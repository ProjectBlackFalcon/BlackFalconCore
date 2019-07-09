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
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time, 'game_state': (game_state['pos'], game_state['worldmap'], game_state['cell'])}
    }
    log.close_logger(logger)
    return strategy