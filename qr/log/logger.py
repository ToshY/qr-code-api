import logging
import sys


def get_stream_handler(formatter, log_level=logging.DEBUG, stream=sys.stdout):
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    return stream_handler


def get_logger(name, formatter, log_level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    if not logger.handlers:
        logger.addHandler(get_stream_handler(formatter, log_level))
    return logger
