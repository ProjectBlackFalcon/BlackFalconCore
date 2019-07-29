import json
import math
import time

import strategies
from strategies import support_functions, auctionh_get_prices
from tools import logger as log


def auctionh_sell(**kwargs):
    """
    Sells items at this map's auction house

    :param kwargs:
    :return: report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])
    start, global_start = time.time(), time.time()

    # Establish the list of stuff to sell
    stuff_to_sell = {}
    for item in strategy['parameters']['items']:

        # If both a general and unique id are given
        if 'general_id' in item.keys() and item['general_id'] is not None and \
                'unique_id' in item.keys() and item['unique_id'] is not None:
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': 'General id and unique id can not both be specified for an item'}
            }
            log.close_logger(logger)
            return strategy

        # If a general id is given
        if 'general_id' in item.keys() and item['general_id'] is not None:
            for inventory_item in listener.game_state['inventory']:
                if inventory_item['objectGID'] == item['general_id'] and inventory_item['position'] == 63:
                    item['name'] = assets['id_2_names'][str(inventory_item['objectGID'])]
                    item['type'] = assets['id_2_type'][str(inventory_item['objectGID'])]
                    stuff_to_sell[inventory_item['objectUID']] = item

        # If a unique is is given
        if 'unique_id' in item.keys() and item['unique_id'] is not None:
            found = False
            for inventory_item in listener.game_state['inventory']:
                if inventory_item['objectUID'] == item['unique_id']:
                    if inventory_item['position'] != 63:
                        logger.warning('Item is currently worn and cannot be sold')
                        strategy['report'] = {
                            'success': False,
                            'details': {'Execution time': time.time() - start, 'Reason': 'Item is currently worn and cannot be sold'}
                        }
                        log.close_logger(logger)
                        return strategy

                    found = True
                    item['name'] = assets['id_2_names'][str(inventory_item['objectGID'])]
                    item['type'] = assets['id_2_type'][str(inventory_item['objectGID'])]
                    item['general_id'] = inventory_item['objectGID']
                    stuff_to_sell[inventory_item['objectUID']] = item

            if not found:
                logger.warning('Item specified by unique id could not be found in inventory')
                strategy['report'] = {
                    'success': False,
                    'details': {'Execution time': time.time() - start,
                                'Reason': 'Item specified by unique id could not be found in inventory'}
                }
                log.close_logger(logger)
                return strategy

    # Check quantities
    for uid, item in stuff_to_sell.items():
        if 'quantity' not in item.keys():
            item['quantity'] = 'all'

        available_in_inv = 0
        for inventory_item in listener.game_state['inventory']:
            if inventory_item['objectUID'] == uid:
                available_in_inv = inventory_item['quantity']
                break

        if item['quantity'] == 'all':
            item['quantity'] = available_in_inv // item['pack_size']
        elif item['quantity'] * item['pack_size'] > available_in_inv:
            logger.warning('Not enough {}/{}. Requested {}, available {}'.format(uid, item['name'], item['quantity'] * item['pack_size'], available_in_inv))
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start, 'Reason': 'Not enough {}/{}. Requested {}, available {}'.format(uid, item['name'], item['quantity'] * item['pack_size'], available_in_inv)}
            }
            log.close_logger(logger)
            return strategy

    # Fill prices
    for uid, item in stuff_to_sell.items():
        prices_to_check = []
        if 'price' not in item.keys():
            prices_to_check.append(item['general_id'])

    sub_strategy = strategies.auctionh_get_prices.auctionh_get_prices(
        assets=assets,
        orders_queue=orders_queue,
        listener=listener,
        strategy={
            'bot': strategy['bot'],
            'parameters': {
                'general_ids_list': prices_to_check
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

    for gid, item in sub_strategy['report']['details']['Results'].items():
        gid = int(gid)
        for uid, item_to_sell in stuff_to_sell.items():
            if gid == item_to_sell['id'] and 'price' not in item_to_sell.keys():
                item_to_sell['price'] = item['item_stats'][0]['prices'][[1, 10, 100].index(item_to_sell['pack_size'])] - 1

    # Check that the bot has enough money to sell
    total_fee = 0
    for uid, item in stuff_to_sell.items():
        total_fee += math.ceil(item['price'] * item['quantity'] * 0.2)
    if total_fee > listener.game_state['kamas']:
        logger.warning('Not enough money to sell items. Needed: {}, available: {}. Items to sell: {}'.format(total_fee, listener.game_state['kamas'], stuff_to_sell))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start,
                        'Reason': 'Item specified by unique id could not be found in inventory'}
        }
        log.close_logger(logger)
        return strategy

    # Open the auction house if it is closed.
    if not listener.game_state['auction_house_info']:
        sub_strategy = strategies.auctionh_open.auctionh_open(
            listener=listener,
            orders_queue=orders_queue,
            assets=assets,
            strategy={
                "bot": strategy['bot'],
                "parameters": {
                    "mode": "sell"
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

    # TODO: Check that the hdv has the level to sell these items

    # Check that the hdv can sell these items
    for uid, item in stuff_to_sell.items():
        if item['type'] not in listener.game_state['auction_house_info']['sellerDescriptor']['types']:
            logger.warning('Type {} can not be sold at the {} auction house'.format(item['type'], listener.game_state['pos']))
            strategy['report'] = {
                'success': False,
                'details': {'Execution time': time.time() - start,
                            'Reason': 'Type {} can not be sold at the {} auction house'.format(item['type'], listener.game_state['pos'])}
            }
            log.close_logger(logger)
            return strategy

    # Check that the bot has enough slots available
    total_slots_needed = 0
    for uid, item in stuff_to_sell.items():
        total_slots_needed += item['quantity']

    available_slots = listener.game_state['auction_house_info']['sellerDescriptor']['maxItemPerAccount'] - len(listener.game_state['auction_house_info']['sellerDescriptor']['objectsInfos'])  # TODO: verify that
    if total_slots_needed > available_slots:
        logger.warning('Not enough slots available to sell items. Needed: {}, available: {}. Items to sell: {}'.format(total_slots_needed, available_slots, stuff_to_sell))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': time.time() - start,
                        'Reason': 'Not enough slots available to sell items. Needed: {}, available: {}. Items to sell: {}'.format(total_slots_needed, available_slots, stuff_to_sell)}
        }
        log.close_logger(logger)
        return strategy


    # TODO: sell stuff
