import json
import time

import strategies
from strategies import support_functions
from tools import logger as log


def connect(**kwargs):
    """
    A strategy to connect a bot.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    if support_functions.get_profile(strategy['bot'])['banned']:
        logger.warning('{} has been banned'.format(strategy['bot']))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': '{} has been banned'.format(strategy['bot'])}
        }
        log.close_logger(logger)
        return strategy

    if 'connected' in listener.game_state.keys():
        if listener.game_state['connected']:
            logger.info('Bot connected in {}s'.format(0))
            strategy['report'] = {
                'success': True,
                'details': {'Execution time': 0}
            }
            log.close_logger(logger)
            return strategy

    bot_profile = strategies.support_functions.get_profile(strategy['bot'])
    order = {
        'command': 'connect',
        'parameters': {
            'name': bot_profile['name'],
            'username': bot_profile['username'],
            'password': bot_profile['password'],
            'serverId': assets['server_2_id'][bot_profile['server']],
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 40 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'connected' in listener.game_state.keys() and 'api_outdated' in listener.game_state.keys():
            if 'pos' in listener.game_state.keys() or listener.game_state['api_outdated'] or listener.game_state['banned']:
                # Actually wait for the map to load and not just a connection confirmation
                waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed connecting in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
        }
        log.close_logger(logger)
        return strategy

    if listener.game_state['api_outdated']:
        logger.warn('Your BlackFalconAPI is outdated. Try to get the latest one or contact the BlackFalcon team if you already have the latest version')
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Your BlackFalconAPI is outdated. Try to get the latest one or contact the BlackFalcon team if you already have the latest version'}
        }
        log.close_logger(logger)
        return strategy

    if listener.game_state['banned']:
        logger.warn('{} has been banned'.format(strategy['bot']))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': '{} has been banned'.format(strategy['bot'])}
        }
        log.close_logger(logger)
        return strategy

    logger.info('Connected {} in {}s'.format(strategy['bot'], execution_time))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }
    log.close_logger(logger)
    return strategy
