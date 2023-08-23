import datetime
import logging
import os
import sys

import pytz

WALL_E_LOG_HANDLER_NAME = "wall_e"

date_timezone = pytz.timezone('US/Pacific')

barrier_logging_level = logging.ERROR


class WalleDebugStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno < barrier_logging_level:
            super().emit(record)


class PSTFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super(PSTFormatter, self).__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):  # noqa: N802
        dt = datetime.datetime.fromtimestamp(record.created, self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return str(dt)


REDIRECT_STD_STREAMS = True
date_formatting_in_log = '%Y-%m-%d %H:%M:%S'
date_formatting_in_filename = "%Y_%m_%d_%H_%M_%S"
modular_log_prefix = "cmd_"
sys_stream_formatting = PSTFormatter(
    '%(asctime)s = %(levelname)s = %(name)s = %(message)s', date_formatting_in_log, tz=date_timezone
)


class Loggers:
    loggers = []
    logger_list_indices = {}

    @classmethod
    def get_logger(cls, logger_name):
        if logger_name == WALL_E_LOG_HANDLER_NAME:
            return cls._setup_wall_e_logger()
        else:
            return cls._setup_logger(logger_name)

    @classmethod
    def _setup_wall_e_logger(cls):
        date = datetime.datetime.now(date_timezone).strftime(date_formatting_in_filename)
        if not os.path.exists(f"logs/{WALL_E_LOG_HANDLER_NAME}"):
            os.makedirs(f"logs/{WALL_E_LOG_HANDLER_NAME}")
        if not os.path.exists(f"logs/{WALL_E_LOG_HANDLER_NAME}"):
            os.makedirs(f"logs/{WALL_E_LOG_HANDLER_NAME}")

        sys_logger = logging.getLogger(WALL_E_LOG_HANDLER_NAME)
        sys_logger.setLevel(logging.DEBUG)

        debug_log_file_absolute_path = (
            f"logs/{WALL_E_LOG_HANDLER_NAME}/{date}_debug.log"
        )
        sys_stream_error_log_file_absolute_path = (
            f"logs/{WALL_E_LOG_HANDLER_NAME}/{date}_error.log"
        )

        # ensures that anything printed to this logger at level DEBUG or above goes to the specified file
        debug_filehandler = logging.FileHandler(debug_log_file_absolute_path)
        debug_filehandler.setLevel(logging.DEBUG)
        debug_filehandler.setFormatter(sys_stream_formatting)
        sys_logger.addHandler(debug_filehandler)

        # ensures that anything printed to this logger at level ERROR or above goes to the specified file
        error_filehandler = logging.FileHandler(sys_stream_error_log_file_absolute_path)
        error_filehandler.setLevel(barrier_logging_level)
        error_filehandler.setFormatter(sys_stream_formatting)
        sys_logger.addHandler(error_filehandler)

        # ensures that anything from the log goes to the stdout
        if REDIRECT_STD_STREAMS:
            sys.stdout = sys.__stdout__
        sys_stdout_stream_handler = WalleDebugStreamHandler(sys.stdout)
        sys_stdout_stream_handler.setFormatter(sys_stream_formatting)
        sys_stdout_stream_handler.setLevel(logging.DEBUG)
        sys_logger.addHandler(sys_stdout_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stdout = LoggerWriter(sys_logger.info)

        if REDIRECT_STD_STREAMS:
            sys.stderr = sys.__stderr__
        sys_stderr_stream_handler = logging.StreamHandler(sys.stderr)
        sys_stderr_stream_handler.setFormatter(sys_stream_formatting)
        sys_stderr_stream_handler.setLevel(barrier_logging_level)
        sys_logger.addHandler(sys_stderr_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stderr = LoggerWriter(sys_logger.error)

        return sys_logger, debug_log_file_absolute_path, sys_stream_error_log_file_absolute_path

    @classmethod
    def _setup_logger(cls, logger_name):

        date = datetime.datetime.now(date_timezone).strftime(date_formatting_in_filename)
        if not os.path.exists(f"logs/{logger_name}"):
            os.makedirs(f"logs/{logger_name}")
        debug_log_file_absolute_path = f"logs/{logger_name}/{date}_debug.log"
        error_log_file_absolute_path = f"logs/{logger_name}/{date}_error.log"

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        debug_filehandler = logging.FileHandler(debug_log_file_absolute_path)
        debug_filehandler.setLevel(logging.DEBUG)
        debug_filehandler.setFormatter(sys_stream_formatting)
        logger.addHandler(debug_filehandler)

        error_filehandler = logging.FileHandler(error_log_file_absolute_path)
        error_filehandler.setFormatter(sys_stream_formatting)
        error_filehandler.setLevel(barrier_logging_level)
        logger.addHandler(error_filehandler)

        if REDIRECT_STD_STREAMS:
            sys.stdout = sys.__stdout__
        sys_stdout_stream_handler = WalleDebugStreamHandler(sys.stdout)
        sys_stdout_stream_handler.setFormatter(sys_stream_formatting)
        sys_stdout_stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(sys_stdout_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stdout = LoggerWriter(logger.info)

        if REDIRECT_STD_STREAMS:
            sys.stderr = sys.__stderr__
        sys_sterr_stream_handler = logging.StreamHandler(sys.stderr)
        sys_sterr_stream_handler.setFormatter(sys_stream_formatting)
        sys_sterr_stream_handler.setLevel(barrier_logging_level)
        logger.addHandler(sys_sterr_stream_handler)
        if REDIRECT_STD_STREAMS:
            sys.stderr = LoggerWriter(logger.error)

        return logger, debug_log_file_absolute_path, error_log_file_absolute_path

    @classmethod
    def setup_sys_stream_logger(cls):
        cls._setup_wall_e_logger()


class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message)

    def flush(self):
        pass
