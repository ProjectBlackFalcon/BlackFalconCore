import time

from tools import logger as log


def ping(**kwargs):
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']

    logger = log.get_logger(__name__, strategy['bot'])
    last_ping = listener.game_state['ping'] if 'ping' in listener.game_state.keys() else 0

    logger.info('Sending order to bot API: {}'.format('ping'))

    orders_queue.put(('ping',))
    start = time.time()
    waiting = True
    while waiting:
        if 'ping' in listener.game_state.keys():
            if last_ping != listener.game_state['ping']:
                waiting = False
        time.sleep(0.05)
    travel_time = time.time() - start
    logger.info('Received pong response in {}'.format(travel_time))
    strategy['report'] = {
        'success': True,
        'details': 'Response time : {}'.format(travel_time)
    }

    # Properly closing the logger so there are not as many as calls to this function.
    log.close_logger(logger)
    return strategy
