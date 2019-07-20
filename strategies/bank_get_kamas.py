import json
import time

from tools import logger as log
import strategies


def bank_get_kamas(**kwargs):
    """
    A strategy to get kamas from the bank

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    kamas_to_transfer = 'all'
    if 'parameters' in strategy.keys() and 'quantity' in strategy['parameters'].keys() and strategy['parameters']['quantity'] is not None:
        kamas_to_transfer = strategy['parameters']['quantity']

    if not listener.game_state['storage_open']:
        logger.warning('Bank is not open')
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Bank is not open'}
        }
        log.close_logger(logger)
        return strategy

    kamas_in_storage = listener.game_state['storage_content']['kamas']
    kamas_to_transfer = kamas_in_storage if kamas_to_transfer == 'all' else kamas_to_transfer

    if kamas_to_transfer > kamas_in_storage:
        logger.warning('Cannot get {} kamas from bank, only {} are available'.format(kamas_to_transfer, kamas_in_storage))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - global_start, 'Reason': 'Cannot get {} kamas from bank, only {} are available'.format(kamas_to_transfer, kamas_in_storage)}
        }
        log.close_logger(logger)
        return strategy

    if kamas_to_transfer == 0:
        logger.info('No kamas to transfer')
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': time.time() - global_start}
        }
        log.close_logger(logger)
        return strategy

    kamas_before = listener.game_state['kamas']

    order = {
        "command": "move_kamas",
        "parameters": {
            "quantity": -kamas_to_transfer
        }
    }
    logger.info('Sending order to bot API: {}'.format(order))
    orders_queue.put((json.dumps(order),))

    start = time.time()
    timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
    waiting = True
    while waiting and time.time() - start < timeout:
        if 'kamas' in listener.game_state.keys():
            if listener.game_state['kamas'] != kamas_before:
                waiting = False
        time.sleep(0.05)

    execution_time = time.time() - global_start
    if waiting:
        logger.warning('Failed to get {} kamas from bank in {}s'.format(kamas_to_transfer, execution_time))
        strategy['report'] = {
            'success': False,
            'details': {
                'Execution time': execution_time,
                'Reason': 'Failed to get {} from bank in {}s'.format(kamas_to_transfer, execution_time)
            }
        }
        log.close_logger(logger)
        return strategy

    logger.info('{} kamas transferred from bank to inventory'.format(kamas_to_transfer))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy