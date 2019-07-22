import json
import time

from tools import logger as log
import strategies


def auctionh_get_prices(**kwargs):
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

    # Check that the auction house is open
    if not listener.game_state['auction_house_info']:
        logger.warning('Auction house is not open')
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start,
                        'Reason': 'Auction house is not open'}
        }
        log.close_logger(logger)
        return strategy

    ids = []
    if 'parameters' in strategy.keys() and 'general_ids_list' in strategy['parameters']:
        if strategy['parameters']['general_ids_list'] not in [None, 'all']:
            ids = strategy['parameters']['general_ids_list']

        else:
            ids = [int(item_id) for item_id, type_id in assets['id_2_type'].items() if type_id in listener.game_state['auction_house_info']['buyerDescriptor']['types']]
    else:
        ids = [int(item_id) for item_id, type_id in assets['id_2_type'].items() if type_id in listener.game_state['auction_house_info']['buyerDescriptor']['types']]

    id_with_types = {}
    for item_id in ids:
        type_id = assets['id_2_type'][str(item_id)]
        if type_id in id_with_types.keys():
            id_with_types[type_id].append(item_id)
        else:
            id_with_types[type_id] = [item_id]

    for type_id, item_ids in id_with_types.items():
        order = {
            "command": "auctionh_select_category",
            "parameters": {
                "category_id": type_id
            }
        }
        logger.info('Sending order to bot API: {}'.format(order))
        orders_queue.put((json.dumps(order),))
        time.sleep(10)

        # for item_id in item_ids:
        #     order = {
        #         "command": "auctionh_select_item",
        #         "parameters": {
        #             "general_id": item_id
        #         }
        #     }