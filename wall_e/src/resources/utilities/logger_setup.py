import datetime
import logging
import pytz
import sys


class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

    def flush(self):
        pass


def initialize_logger():
    # setting up log requirements
    logger = logging.getLogger('wall_e')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s = %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    sys.stdout = LoggerWriter(logger, logging.INFO)
    sys.stderr = LoggerWriter(logger, logging.WARNING)
    filename = create_log_file(formatter, logger)
    return logger, filename


def create_log_file(formatter, logger):
    date = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y_%m_%d_%H_%M_%S")
    filename = "logs/{}_wall_e".format(date)
    filehandler = logging.FileHandler("{}.log".format(filename))
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return filename
