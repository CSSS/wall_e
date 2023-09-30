import logging

from utilities.global_vars import discordpy_logger, discordpy_logger_name


class DiscordPyDebugStreamHandler(logging.StreamHandler):
    def __init__(self):
        super(DiscordPyDebugStreamHandler, self).__init__()

    def emit(self, record):
        if record.name != discordpy_logger_name:
            for handler in discordpy_logger.handlers:
                if record.levelno >= handler.level:
                    handler.emit(record)
