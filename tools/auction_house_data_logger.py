import logging
import sys
import logstash
from credentials import credentials


def get_logger(file_name, bot_name):
    """
    Provides a logger to keep a trace of what is happening in a file. It is recommended to use the logger provided by this function instead of prints.

    :param file_name: Just pass __name__ here.
    :param bot_name: The name of the bot running
    :return: A logger object
    """
    logger = logging.getLogger(file_name + ' ' + bot_name)
    logger.setLevel(logging.DEBUG)

    handler = logstash.LogstashHandler(credentials['logstash']['host'], credentials['logstash']['auctionhousedataport'], version=1)

    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def close_logger(logger):
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)
