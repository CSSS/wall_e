import datetime
import logging
import pytz
import sys

from resources.utilities.logger_setup import LoggerWriter


##################
# LOGGING SETUP ##
##################
def initalizeLogger():
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
    FILENAME = createLogFile(formatter, logger)
    return logger, FILENAME


def createLogFile(formatter, logger):
    DATE = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y_%m_%d_%H_%M_%S")
    FILENAME = "logs/" + DATE + "_wall_e"
    filehandler = logging.FileHandler("{}.log".format(FILENAME))
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return FILENAME
