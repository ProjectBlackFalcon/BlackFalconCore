import json
import time

from tools import logger as log
import strategies


def auctionh_open(**kwargs):
    """
    A strategy to open the auction house.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()
    mode = 'buy'
    if 'parameters' in strategy.keys() and 'mode' in strategy['parameters'].keys():
        if strategy['parameters']['mode'] not in ['buy', 'sell', None]:
            logger.warning('\'mode\' parameter should be \'buy\' or \'sell\'')
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': '\'mode\' parameter should be \'buy\' or \'sell\''}
            }
            log.close_logger(logger)
            return strategy
        elif strategy['parameters']['mode'] == 'sell':
            mode = 'sell'

    if not listener.game_state['auction_house_info']:
        # Get the IDs for activating the interactive
        element_id, skill_uid = None, None
        current_map = listener.game_state['pos']
        for element in listener.game_state['map_elements']:
            if 'enabledSkills' in element.keys():
                for skill in element['enabledSkills']:
                    if 'skillId' in skill.keys() and skill['skillId'] == 355:
                        element_id = element['elementId']
                        skill_uid = skill['skillInstanceUid']

        if element_id is None or skill_uid is None:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': 'Could not find an auction house at {}, map id : {}'.format(current_map, listener.game_state['map_id'])}
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
            if 'auction_house_info' in listener.game_state.keys():
                if listener.game_state['auction_house_info']:
                    waiting = False
            time.sleep(0.05)
        execution_time = time.time() - start

        if waiting:
            logger.warn('Failed opening the auction house in {}s'.format(execution_time))
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': execution_time, 'Reason': 'Timeout'}
            }
            log.close_logger(logger)
            return strategy

    logger.info('Opened auction house {}s'.format(time.time() - global_start))

    if listener.game_state['auction_house_mode'] != mode:
        action_id = 5 if mode == 'sell' else 6
        order = {
            "command": "open_npc",
            "parameters": {
                "map_id": listener.game_state['map_id'],
                "npc_id": -1,
                "action_id": action_id
            }
        }
        logger.info('Sending order to bot API: {}'.format(order))
        orders_queue.put((json.dumps(order),))

        start = time.time()
        timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
        waiting = True
        while waiting and time.time() - start < timeout:
            if 'auction_house_mode' in listener.game_state.keys():
                if listener.game_state['auction_house_mode'] == mode:
                    waiting = False
            time.sleep(0.05)
        execution_time = time.time() - start

        if waiting:
            logger.warn('Failed setting the auction house mode to {} in {}s'.format(mode, execution_time))
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': execution_time, 'Reason': 'Failed setting the auction house mode to {} in {}s'.format(mode, execution_time)}
            }
            log.close_logger(logger)
            return strategy
        logger.info('Set auction house mode to {} in {}s'.format(mode, time.time() - start))

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy