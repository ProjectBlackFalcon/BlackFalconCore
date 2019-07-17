import json
import time

import strategies
from strategies import support_functions
from tools import logger as log


def use_zaap(**kwargs):
    """
    Uses a zaap to get to a specified destination
    The bot must be on a map with a zaap
    This strategy will move the bot to an appropriate cell to use the zaap

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    resource_cell = strategy['parameters']['cell']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    # TODO: Check if the cell has an available resource
    element_id = None
    for element in listener.game_state['stated_elements']:
        if element['elementCellId'] == resource_cell:
            element_id = element['elementId']
    if element_id is None:
        logger.warn('Did not find a resource at cell {} in {}s'.format(resource_cell, 0))
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Did not find a resource at cell {} in {}s'.format(resource_cell, 0)}
        }
        return strategy

    skill_id, skill_uid = None, None
    for element in listener.game_state['map_elements']:
        if element_id == element['elementId']:
            if 'enabledSkills' in element.keys():
                if 'skillId' in element['enabledSkills'].keys():
                    skill_id = element['enabledSkills']['skillId']
                    skill_uid = element['enabledSkills']['skillInstanceUid']
    if skill_id is None:
        logger.warn('Resource at cell {} is not harvestable')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Resource at cell {} is not harvestable'}
        }
        return strategy

    # TODO: Check if the player has the skill level to harvest it
    required_skill_level, range = None, None
    for skill in assets['Skills']:
        if skill['id'] == skill_id:
            required_skill_level = skill['levelMin']
            range = skill['range']
    if required_skill_level is None:
        logger.warn('Skill id not found')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Skill id not found'}
        }
        return strategy

    bot_skill_level = None
    for job_id, job in listener.game_state['jobs'].items():
        for skill in job['skills']:
            if skill['skillId'] == skill_id:
                bot_skill_level = job['jobLevel']
    if bot_skill_level is None:
        logger.warn('Could not determine bot skill level')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Could not determine bot skill level'}
        }
        return strategy

    if bot_skill_level < required_skill_level:
        logger.warn('Bot skill level insufficient')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Bot skill level insufficient'}
        }
        return strategy

    # TODO: Check if the player can reach the resource i.e. skill range >= manhattan distance between closest reachable cell and resource cell
    # TODO: Move the bot the appropriate cell to use the resource
    # TODO: Check if the resource is still available
    # TODO: harvest

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
        if listener.game_state['harvest_done']:
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to perform harvest in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed to perform harvest in {}s'.format(execution_time)}
        }
        return strategy

    logger.info('Harvested in {}s'.format(execution_time))

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time}
    }

    log.close_logger(logger)
    return strategy