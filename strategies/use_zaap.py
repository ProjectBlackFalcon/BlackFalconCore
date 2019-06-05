import json
import time

from tools import logger as log


def use_zaap(**kwargs):
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot']['name'])

    # TODO: check that the player is besides a zaap activable

    zaap_id = 0  # TODO: get zaap id from listener
    bot_strategy = {
        'command': 'use_interactive',
        'parameters': {'id': zaap_id, }
    }
    logger.info('Sending order to bot API: {}'.format(json.dumps(bot_strategy)))
    orders_queue.put((json.dumps(bot_strategy),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        # TODO validation condition for zaap menu
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
    # TODO: Select a zaap from the list of possible destinations
    selected_zaap = None
    bot_strategy = {
        'command': 'travel_by_zaap',
        'parameters': {'selected_zaap': selected_zaap}
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