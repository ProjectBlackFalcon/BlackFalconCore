import json
import time

from tools import logger as log
import strategies


def bank_get_items(**kwargs):
    """
    A strategy to get items from the bank

    :param kwargs: strategy, listener, and orders_queue
    :return: the input strategy with a report
    """
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    logger = log.get_logger(__name__, strategy['bot'])

    global_start, start = time.time(), time.time()

    items_to_transfer = {}
    if 'parameters' in strategy.keys() and 'items' in strategy['parameters'].keys():
        if strategy['parameters']['items'] != 'all' and strategy['parameters']['items'] is not None:
            for item in strategy['parameters']['items']:
                items_to_transfer[item['general_id']] = item['quantity'] if 'quantity' in item.keys() else 'all'
        else:
            items_to_transfer = 'all'
    else:
        items_to_transfer = 'all'

    if not listener.game_state['storage_open']:
        logger.warning('Bank is not open')
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Bank is not open'}
        }
        log.close_logger(logger)
        return strategy

    # Check that all requested items with a specified quantity are in the storage
    if type(items_to_transfer) is dict:
        for key in items_to_transfer.keys():
            found = False
            for item in listener.game_state['storage_content']['objects']:
                if item['objectGID'] == key:
                    found = True
            if not found:
                logger.warning('Object {}/{} with requested quantity {} is not in the storage'.format(key, assets['id_2_names'][str(key)], items_to_transfer[key]))
                strategy['report'] = {
                    'success': False,
                    'details': {'Execution time': 0, 'Reason': 'Object {}/{} with requested quantity {} is not in the storage'.format(key, assets['id_2_names'][str(key)], items_to_transfer[key])}
                }
                log.close_logger(logger)
                return strategy

    uids_to_transfer_all = []
    uids_to_transfer_specified = []
    transfer_recap = []
    for item in listener.game_state['storage_content']['objects']:
        if items_to_transfer == 'all':
            transfer_recap.append({
                'GID': item['objectGID'],
                'name': assets['id_2_names'][str(item['objectGID'])],
                'quantity': item['quantity'],
                'weight_one': assets['id_2_weight'][str(item['objectGID'])]
            })

            uids_to_transfer_all.append(item['objectUID'])
        elif item['objectGID'] in items_to_transfer.keys():
            transfer_recap.append({
                'GID': item['objectGID'],
                'quantity': item['quantity'],
                'weight_one': assets['id_2_weight'][str(item['objectGID'])]
            })

            if items_to_transfer[item['objectGID']] == 'all':
                uids_to_transfer_all.append(item['objectUID'])
            elif items_to_transfer[item['objectGID']] > 0:
                if item['quantity'] < items_to_transfer[item['objectGID']]:
                    logger.warning('Requested quantity of {} {}:{} is not available in storage ({} available )'.format(items_to_transfer[item['objectGID']], item['objectGID'], assets['id_2_names'][str(item['objectGID'])], item['quantity']))
                    strategy['report'] = {
                        'success': False,
                        'details': {'Execution time': 0, 'Reason': 'Requested quantity of {} {}/{} is not available in storage ({} available )'.format(items_to_transfer[item['objectGID']], item['objectGID'], assets['id_2_names'][str(item['objectGID'])], item['quantity'])}
                    }
                    log.close_logger(logger)
                    return strategy

                uids_to_transfer_specified.append({
                    'unique_id': item['objectUID'],
                    'quantity': items_to_transfer[item['objectGID']]
                })
                transfer_recap[-1]['quantity'] = items_to_transfer[item['objectGID']]

    # Check weight
    available_weight = listener.game_state['max_weight'] - listener.game_state['weight']
    transfer_weight = sum([item['quantity'] * item['weight_one'] for item in transfer_recap])
    if transfer_weight > available_weight:
        logger.warning('Requested transfer ({} pods) would exceed carry capacity ({} pods)'.format(transfer_weight, available_weight))
        strategy['report'] = {
            'success': False,
            'details': {'Execution time': 0, 'Reason': 'Requested transfer ({} pods) would exceed carry capacity ({} pods)'.format(transfer_weight, available_weight)}
        }
        log.close_logger(logger)
        return strategy

    # Transfer pack (quantity unspecified)
    if len(uids_to_transfer_all):
        inventory_before = json.loads(json.dumps(listener.game_state['inventory']))
        order = {
            "command": "storage_to_inv_list",
            "parameters": {
                "items_uids": uids_to_transfer_all
            }
        }
        logger.info('Sending order to bot API: {}'.format(order))
        orders_queue.put((json.dumps(order),))

        start = time.time()
        timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
        waiting = True
        while waiting and time.time() - start < timeout:
            if listener.game_state['inventory'] != inventory_before:
                waiting = False
            time.sleep(0.05)

        execution_time = time.time() - global_start
        if waiting:
            logger.warning('Failed to get pack of items {} from bank in {}s'.format(uids_to_transfer_all, execution_time))
            strategy['report'] = {
                'success': False,
                'details': {
                    'Execution time': execution_time,
                    'Reason': 'Failed to get pack of items {} from bank in {}s'.format(uids_to_transfer_all, execution_time)
                }
            }
            log.close_logger(logger)
            return strategy

    # Transfer specified
    for item in uids_to_transfer_specified:
        inventory_before = json.loads(json.dumps(listener.game_state['inventory']))
        order = {
            "command": "storage_to_inv",
            "parameters": {
                "item_uid": item['unique_id'],
                "quantity": item['quantity']
            }
        }
        logger.info('Sending order to bot API: {}'.format(order))
        orders_queue.put((json.dumps(order),))

        start = time.time()
        timeout = 10 if 'timeout' not in strategy.keys() else strategy['timeout']
        waiting = True
        while waiting and time.time() - start < timeout:
            if listener.game_state['inventory'] != inventory_before:
                waiting = False
            time.sleep(0.05)

        execution_time = time.time() - global_start
        if waiting:
            logger.warning('Failed to get {} item {} from bank in {}s'.format(item['quantity'], item['unique_id'], execution_time))
            strategy['report'] = {
                'success': False,
                'details': {
                    'Execution time': execution_time,
                    'Reason': 'Failed to get {} item {} from bank in {}s'.format(item['quantity'], item['unique_id'], execution_time)
                }
            }
            log.close_logger(logger)
            return strategy

    logger.info('Transferred from storage to inventory: {}'.format(transfer_recap))
    strategy['report'] = {
        'success': True,
        'details': {'Execution time': time.time() - global_start, 'Transfer': transfer_recap}
    }
    log.close_logger(logger)
    return strategy