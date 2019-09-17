import json

import time

from tools import logger as log
import strategies
from strategies import support_functions


def auctionh_get_prices(**kwargs):
    """
    A strategy to get prices from the auction house.

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    sample_timestamp = int(time.time())
    if 'sample_timestamp' in strategy['parameters']:
        sample_timestamp = strategy['parameters']['sample_timestamp']

    # Check that the auction house is open. If it is, close it and open it again.
    # This is to prevent some edge case of item or type selection. See todos, lower in this script.
    if not listener.game_state['auction_house_info']:
        sub_strategy = strategies.auctionh_open.auctionh_open(
            listener=listener,
            orders_queue=orders_queue,
            assets=assets,
            strategy={
                "bot": strategy['bot'],
                "parameters": {
                    "mode": "buy"
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

    else:
        sub_strategy = strategies.auctionh_close.auctionh_close(
            listener=listener,
            orders_queue=orders_queue,
            assets=assets,
            strategy={
                "bot": strategy['bot'],
            }
        )
        if not sub_strategy['report']['success']:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': sub_strategy['report']}
            }
            log.close_logger(logger)
            return strategy

        sub_strategy = strategies.auctionh_open.auctionh_open(
            listener=listener,
            orders_queue=orders_queue,
            assets=assets,
            strategy={
                "bot": strategy['bot'],
                "parameters": {
                    "mode": "buy"
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

    if 'parameters' in strategy.keys() and 'general_ids_list' in strategy['parameters']:
        if strategy['parameters']['general_ids_list'] not in [None, 'all']:
            ids = strategy['parameters']['general_ids_list']

        else:
            ids = 'all'
    else:
        ids = 'all'

    all = False
    if ids == 'all':
        all = True
        actual_ids = []
        for item_id, type_id in assets['id_2_type'].items():
            if type_id in listener.game_state['auction_house_info']['buyerDescriptor']['types']:
                item_level = assets['id_2_level'][str(item_id)]
                if item_level <= 60 or listener.game_state['sub_end']:
                    actual_ids.append(int(item_id))
        ids = actual_ids

    id_with_types = {}
    for item_id in ids:
        type_id = assets['id_2_type'][str(item_id)]
        if type_id in id_with_types.keys():
            id_with_types[type_id].append(item_id)
        else:
            id_with_types[type_id] = [item_id]

    results = {}
    for type_id, item_ids in id_with_types.items():
        previous_available_ids = listener.game_state['auction_house_info']['items_available'] if 'items_available' in listener.game_state['auction_house_info'].keys() else []
        order = {
            "command": "auctionh_select_category",
            "parameters": {
                "category_id": type_id
            }
        }
        logger.info('Sending order to bot API: {}'.format(order))
        orders_queue.put((json.dumps(order),))
        start = time.time()
        timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
        waiting = True
        while waiting and time.time() - start < timeout:
            if 'auction_house_info' in listener.game_state.keys() and 'items_available' in listener.game_state['auction_house_info']:
                # TODO: This test is going to wrongly fail if asked to switch from a category to the same one
                if listener.game_state['auction_house_info']['items_available'] != previous_available_ids:
                    waiting = False
            time.sleep(0.05)
        execution_time = time.time() - start

        if waiting:
            logger.warn('Failed to change categories in {}s'.format(execution_time))
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': execution_time, 'Reason': 'Failed to change categories'}
            }
            log.close_logger(logger)
            return strategy

        for item_id in item_ids:
            if item_id in listener.game_state['auction_house_info']['items_available']:
                previous_available_ids = str(listener.game_state['auction_house_info']['item_selected'][-1]) if 'item_selected' in listener.game_state['auction_house_info'].keys() else []
                order = {
                    "command": "auctionh_select_item",
                    "parameters": {
                        "general_id": item_id
                    }
                }
                logger.info('Sending order to bot API: {}'.format(order))
                orders_queue.put((json.dumps(order),))

                start = time.time()
                timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
                waiting = True
                while waiting and time.time() - start < timeout:
                    if 'auction_house_info' in listener.game_state.keys() and 'item_selected' in listener.game_state['auction_house_info']:
                        # TODO: This test is going to wrongly fail if asked to switch from an item to the same one
                        if str(listener.game_state['auction_house_info']['item_selected'][-1]) != str(previous_available_ids):
                            waiting = False
                    time.sleep(0.05)
                execution_time = time.time() - start

                if waiting:
                    logger.warn('Failed to select item')
                    strategy['report'] = {
                        'success': False,
                        'details': {'Execution time': execution_time, 'Reason': 'Failed to select item'}
                    }
                    log.close_logger(logger)
                    return strategy

                results[item_id] = {
                    'item_name': assets['id_2_names'][str(item_id)],
                    'items_stats': listener.game_state['auction_house_info']['actual_item_selected']
                }

    if all:
        object_type = 'resource'
        if int(list(results.keys())[0]) in assets['hdv_2_id']['Equipements']:
            object_type = 'item'

        n_new_entries = support_functions.log_prices(object_type, results, listener.game_state['server'], sample_timestamp)
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': time.time() - global_start, 'Number of new entries': n_new_entries}
        }
    else:
        strategy['report'] = {
            'success': True,
            'details': {'Execution time': time.time() - global_start, 'Results': results}
        }
    log.close_logger(logger)
    return strategy