import json
import time

import strategies
from strategies import support_functions
from tools import logger as log


def harvest(**kwargs):
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

    # Manage whitelist/blacklist
    if 'whitelist' in strategy['parameters'].keys() and \
            strategy['parameters']['whitelist'] is not None and \
            'blacklist' in strategy['parameters'].keys() and \
            strategy['parameters']['blacklist'] is not None:
        logger.warn('You can not have a whitelist and a blacklist at the same time')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'You can not have a whitelist and a blacklist at the same time'}
        }
        log.close_logger(logger)
        return strategy

    if 'whitelist' in strategy['parameters'].keys() and strategy['parameters']['whitelist'] is not None:
        whitelist = strategy['parameters']['whitelist']
    elif 'blacklist' in strategy['parameters'].keys() and strategy['parameters']['blacklist'] is not None:
        whitelist = [int(key) for key in assets['id_2_names'].keys() if key not in strategy['parameters']['blacklist']]
    else:
        whitelist = [int(key) for key in assets['id_2_names'].keys()]

    # Check if the cell has an available resource
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
        log.close_logger(logger)
        return strategy

    skill_id, skill_uid = None, None
    for element in listener.game_state['map_elements']:
        if element_id == element['elementId']:
            if 'enabledSkills' in element.keys():
                for skill in element['enabledSkills']:
                    if 'skillId' in skill.keys():
                        skill_id = skill['skillId']
                        skill_uid = skill['skillInstanceUid']
    if skill_id is None:
        logger.warn('Resource at cell {} is not harvestable'.format(resource_cell))
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Resource at cell {} is not harvestable'.format(resource_cell)}
        }
        log.close_logger(logger)
        return strategy

    # Check if the resource is whitelisted
    for skill in assets['Skills']:
        if skill['id'] == skill_id and skill['gatheredRessourceItem'] not in whitelist:
            logger.warn('Resource ({}/{}) at cell {} is not whitelisted'.format(skill['gatheredRessourceItem'], assets['id_2_names'][str(skill['gatheredRessourceItem'])], resource_cell))
            strategy['report'] = {
                'success': False,
                'details': {'Reason': 'Resource ({}/{}) at cell {} is not whitelisted'.format(skill['gatheredRessourceItem'], assets['id_2_names'][str(skill['gatheredRessourceItem'])], resource_cell)}
            }
            log.close_logger(logger)
            return strategy

    # Check if the player has the skill level to harvest it
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
        log.close_logger(logger)
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
        log.close_logger(logger)
        return strategy

    if bot_skill_level < required_skill_level:
        logger.warn('Bot skill level insufficient')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Bot skill level insufficient'}
        }
        log.close_logger(logger)
        return strategy

    # TODO: remove this after fight is implemented
    if bot_skill_level > 19:
        logger.warn('Bot skill level too high')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Bot skill level too high'}
        }
        log.close_logger(logger)
        return strategy

    # Check if the player can reach the resource i.e. skill range >= manhattan distance between closest reachable cell and resource cell
    closest_reachable_cell = support_functions.get_closest_reachable_cell(assets['map_info'], resource_cell, listener.game_state['cell'], listener.game_state['pos'], listener.game_state['worldmap'])
    dist = sum([abs(a - b) for a, b in zip(support_functions.cell_2_coord(closest_reachable_cell), support_functions.cell_2_coord(resource_cell))])
    if dist > range:
        logger.warn('Resource out of range')
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Resource out of range'}
        }
        log.close_logger(logger)
        return strategy

    # Move the bot the appropriate cell to use the resource
    sub_strategy = strategies.move.move(
        listener=listener,
        strategy={'bot': strategy['bot'], 'parameters': {'cell': closest_reachable_cell}},
        orders_queue=orders_queue,
        assets=assets
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': 'Move to get to resource harvest spot failed'}
        }
        log.close_logger(logger)
        return strategy

    # Check if the resource is still available
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
        log.close_logger(logger)
        return strategy

    skill_id, skill_uid = None, None
    for element in listener.game_state['map_elements']:
        if element_id == element['elementId']:
            if 'enabledSkills' in element.keys():
                for skill in element['enabledSkills']:
                    if 'skillId' in skill.keys():
                        skill_id = skill['skillId']
                        skill_uid = skill['skillInstanceUid']
    if skill_id is None:
        logger.warn('Resource at cell {} is not harvestable'.format(resource_cell))
        strategy['report'] = {
            'success': False,
            'details': {'Reason': 'Resource at cell {} is not harvestable'.format(resource_cell)}
        }
        log.close_logger(logger)
        return strategy

    # harvest
    inventory_before_harvest = json.loads(json.dumps(listener.game_state['inventory']))
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
        if listener.game_state['harvest_started']:
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Failed to start harvest in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time, 'Reason': 'Failed to start harvest in {}s'.format(execution_time)}
        }
        log.close_logger(logger)
        return strategy

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if listener.game_state['harvest_done']:
            waiting = False
        time.sleep(0.05)
    execution_time = time.time() - start

    if waiting:
        logger.warn('Harvest started but did not end ? in {}s'.format(execution_time))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': execution_time,
                        'Reason': 'Harvest started but did not end ? in {}s'.format(execution_time)}
        }
        log.close_logger(logger)
        return strategy

    collected = {}
    inventory_after_harvest = json.loads(json.dumps(listener.game_state['inventory']))
    for item in inventory_after_harvest:
        was_in_inventory = False
        for item_before in inventory_before_harvest:
            if item['objectUID'] == item_before['objectUID']:
                was_in_inventory = True
                if item['quantity'] != item_before['quantity']:
                    if assets['id_2_names'][str(item['objectGID'])] in collected.keys():
                        collected[assets['id_2_names'][str(item['objectGID'])]] += item['quantity'] - item_before['quantity']
                    else:
                        collected[assets['id_2_names'][str(item['objectGID'])]] = item['quantity'] - item_before['quantity']

        if not was_in_inventory:
            collected[assets['id_2_names'][str(item['objectGID'])]] = item['quantity']

    logger.info('Harvested {} in {}s'.format(collected, execution_time))

    strategy['report'] = {
        'success': True,
        'details': {
            'Execution time': execution_time,
            'Collected': collected
        }
    }

    log.close_logger(logger)
    return strategy