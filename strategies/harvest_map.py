import json
import time

import strategies
from strategies import support_functions
from tools import logger as log


def harvest_map(**kwargs):
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

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    resource_cells = []
    for element in listener.game_state['stated_elements']:
        resource_cells.append(element['elementCellId'])

    path = []
    if len(resource_cells):
        closest, distance = resource_cells[0], support_functions.distance_cell(resource_cells[0], listener.game_state['cell'])
        for cell in resource_cells:
            if support_functions.distance_cell(cell, listener.game_state['cell']) < distance:
                closest, distance = cell, support_functions.distance_cell(cell, listener.game_state['cell'])
        path = [closest]
        del resource_cells[resource_cells.index(closest)]

    while len(resource_cells):
        closest, distance = resource_cells[0], support_functions.distance_cell(resource_cells[0], path[-1])
        for cell in resource_cells:
            if support_functions.distance_cell(cell, path[-1]) < distance:
                closest, distance = cell, support_functions.distance_cell(cell, path[-1])
        path.append(closest)
        del resource_cells[resource_cells.index(closest)]

    collected, failures, success = {}, [], 0
    for cell in path:
        sub_strategy = strategies.harvest.harvest(
            listener=listener,
            strategy={'bot': strategy['bot'], 'parameters': {'cell': cell}},
            orders_queue=orders_queue,
            assets=assets
        )

        if sub_strategy['report']['success']:
            success += 1
            for item, quantity in sub_strategy['report']['details']['Collected'].items():
                if item in collected.keys():
                    collected[item] += quantity
                else:
                    collected[item] = quantity
        else:
            failures.append(sub_strategy['report']['details']['Reason'])

    execution_time = time.time() - global_start
    logger.info('Harvested {} in {}s'.format(collected, execution_time))

    strategy['report'] = {
        'success': True,
        'details': {
            'Execution time': execution_time,
            'Collected': collected,
            'n_collected': success,
            'failures_reasons': failures
        }
    }

    log.close_logger(logger)
    return strategy