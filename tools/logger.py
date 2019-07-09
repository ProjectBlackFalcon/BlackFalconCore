import logging
from logging.handlers import RotatingFileHandler
import sys
import os


def get_logger(file_name, bot_name):
    """
    Provides a logger to keep a trace of what is happening in a file. It is recommended to use the logger provided by this function instead of prints.

    :param file_name: Just pass __name__ here.
    :param bot_name: The name of the bot running
    :return: A logger object
    """
    logger = logging.getLogger(file_name)
    logger.setLevel(logging.DEBUG)
    if 'logs' not in os.listdir('../assets/'):
        os.makedirs('../assets/logs/')
    handler = RotatingFileHandler("../assets/logs/{}.log".format(bot_name), maxBytes=10000000)
    formatter = logging.Formatter('%(asctime)s [%(created).0f]   %(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def close_logger(logger):
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)
