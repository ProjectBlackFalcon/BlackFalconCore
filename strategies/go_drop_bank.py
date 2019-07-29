import json
import time

import strategies
from strategies import support_functions, goto, bank_close, bank_enter, bank_exit, bank_open, bank_put_items, bank_get_kamas
from tools import logger as log


def go_drop_bank(**kwargs):
    """
    Go to the bank to drop what it holds

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    if 'parameters' in strategy.keys() and 'return' in strategy['parameters'].keys() and strategy['parameters']['return'] == 'current':
        strategy['parameters']['return'] = {'pos': listener.game_state['pos'], 'cell': listener.game_state['cell'], 'worldmap': listener.game_state['worldmap']}

    sub_strategy = strategies.goto.goto(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
            'parameters': {
                'x': 4,
                'y': -18,
                'worldmap': 1
            }
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_enter.bank_enter(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_open.bank_open(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_put_items.bank_put_items(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
            'parameters': {
                'items': 'all'
            }
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_get_kamas.bank_get_kamas(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_close.bank_close(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    sub_strategy = strategies.bank_exit.bank_exit(
        orders_queue=orders_queue,
        assets=assets,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
        }
    )
    if not sub_strategy['report']['success']:
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
        }
        log.close_logger(logger)
        return strategy

    if 'parameters' in strategy.keys() and 'return' in strategy['parameters'].keys():
        sub_strategy = strategies.goto.goto(
            orders_queue=orders_queue,
            assets=assets,
            listener=listener,
            strategy={
                'bot': strategy['bot'],
                'parameters': {
                    'x': strategy['parameters']['return']['pos'][0],
                    'y': strategy['parameters']['return']['pos'][1],
                    'cell': strategy['parameters']['return']['cell'] if 'cell' in strategy['parameters']['return'].keys() else None,
                    'worldmap': strategy['parameters']['return']['worldmap'] if 'worldmap' in strategy['parameters']['return'].keys() else 1
                }
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

    logger.info('Dropped to bank in {}s'.format(time.time() - global_start))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start}
    }
    log.close_logger(logger)
    return strategy
