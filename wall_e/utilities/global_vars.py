import os

import django
from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")
django.setup()

application = get_wsgi_application()

from utilities.config.config import WallEConfig # noqa E402
from utilities.setup_logger import Loggers # noqa E402

wall_e_config = WallEConfig(os.environ['basic_config__ENVIRONMENT'])

log_info = Loggers.get_logger(logger_name="sys")
sys_debug_log_file_absolute_path = log_info[1]
sys_error_log_file_absolute_path = log_info[2]

discordpy_logger_name = "discord.py"
discordpy_log_info = Loggers.get_logger(logger_name=discordpy_logger_name)
discordpy_logger = discordpy_log_info[0]
discordpy_debug_log_file_absolute_path = discordpy_log_info[1]
discordpy_error_log_file_absolute_path = discordpy_log_info[2]

log_info = Loggers.get_logger(logger_name="wall_e")

logger = log_info[0]
wall_e_debug_log_file_absolute_path = log_info[1]
wall_e_error_log_file_absolute_path = log_info[2]

from utilities.wall_e_bot import WalleBot # noqa E402

bot = WalleBot()
