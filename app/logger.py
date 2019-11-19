import logging
from logging.handlers import TimedRotatingFileHandler
import os

SERVICE_NAME = os.getenv('SERVICE', 'balancer')
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

FORMATTER = ('%(asctime)s.%(msecs)03dZ [' + SERVICE_NAME +
             '] [%(funcName)s] %(levelname)s: %(message)s')

DATEFMT = '%Y-%m-%dT%H:%M:%S'
format_ = logging.Formatter(FORMATTER, DATEFMT)


def get_console_handler(format_=format_):
    console_handler = logging.StreamHandler(os.sys.stdout)
    console_handler.setFormatter(format_)
    return console_handler


def get_file_handler(format_=format_):
    ROOT_FOLDER = f'/var/log/app/'

    if not os.path.exists(ROOT_FOLDER):
        os.makedirs(ROOT_FOLDER)

    LOG_NAME = ROOT_FOLDER + SERVICE_NAME + '.log'
    
    file_handler = TimedRotatingFileHandler(filename=LOG_NAME,
                                            interval=1,
                                            when='midnight',
                                            backupCount=31)
    file_handler.setFormatter(format_)
    return file_handler


def set_logger(logger_name, file_logging=False):
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, LOGLEVEL))
    logger.addHandler(get_console_handler())
    if file_logging:
        logger.addHandler(get_file_handler())
    logger.propagate = False
    return logger