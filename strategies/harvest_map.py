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

    resource_cell = strategy['parameters']['cell']

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
        closest, distance = resource_cells[0], support_functions.distance_cell(resource_cells[0], listener.game_state['cell'])
        for cell in resource_cells:
            if support_functions.distance_cell(cell, listener.game_state['cell']) < distance:
                closest, distance = cell, support_functions.distance_cell(cell, listener.game_state['cell'])
        path.append(closest)
        del resource_cells[resource_cells.index(closest)]

    logger.debug(path)
    execution_time = time.time() - global_start
    collected = {}
    logger.info('Harvested {} in {}s'.format(collected, execution_time))

    strategy['report'] = {
        'success': True,
        'details': {'Execution time': execution_time, 'Collected': collected}
    }

    log.close_logger(logger)
    return strategy