import importlib
import inspect
import os
import sys
import django
import time

from discord import Intents
from discord.ext import commands
from django.core.wsgi import get_wsgi_application
from resources.utilities.logger_setup import initialize_logger
from resources.utilities.config.config import WallEConfig
from resources.utilities.log_channel import write_to_bot_log_channel

logger, FILENAME = initialize_logger()
wall_e_config = WallEConfig(os.environ['ENVIRONMENT'])

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_db_orm_settings")
django.setup()

from resources.cogs.manage_cog import ManageCog  # noqa: E402

application = get_wsgi_application()

intents = Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)


##################################################
# signals to all functions that use            ##
# "wait_until_ready" that the bot is now ready ##
# to start performing background tasks         ##
##################################################
@bot.event
async def on_ready():
    logger.info('[main.py on_ready()] Logged in as')
    logger.info(f'[main.py on_ready()] {bot.user.name}')
    logger.info(f'[main.py on_ready()] {bot.user.id}')
    logger.info('[main.py on_ready()] ------')
    wall_e_config.set_config_value("bot_profile", "BOT_NAME", bot.user.name)
    wall_e_config.set_config_value("bot_profile", "BOT_AVATAR", bot.user.avatar_url)
    logger.info(
        "[main.py on_ready()] BOT_NAME initialized to"
        f" {wall_e_config.get_config_value('bot_profile', 'BOT_NAME')}"
    )
    logger.info(
        "[main.py on_ready()] BOT_AVATAR initialized to "
        f"{wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR')}"

    )
    logger.info(f"[main.py on_ready()] {bot.user.name} is now ready for commands")


########################################################
# Function that gets called any input or output from ##
# the script					     ##
########################################################
@bot.event
async def on_message(message):
    if message.guild is None and message.author != bot.user:
        await message.author.send("DM has been detected \nUnfortunately none of my developers are smart enough to "
                                  "make me an AI capable of holding a conversation and no one else has volunteered"
                                  " :( \nAll I can say is Harry Potter for life and Long Live Windows Vista!")
    else:
        await bot.process_commands(message)


####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    logger.info("[main.py] Wall-E is starting up")
    # tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info(f"[main.py] trying to open {FILENAME}.log to be able to send "
                    "its output to #bot_log channel")
        f = open(f'{FILENAME}.log', 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel(bot, wall_e_config, f))
        logger.info(
            "[main.py] log file successfully opened and connection to "
            "bot_log channel has been made"
        )
    except Exception as e:
        logger.error(
            "[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
            f"following error {e}")

    # load the code dealing with test server interaction
    try:
        bot.add_cog(ManageCog(bot, wall_e_config))
    except Exception as e:
        exception = f'{type(e).__name_}: {e}'
        logger.error(f'[main.py] Failed to load test server code testenv\n{exception}')

    # removing default help command to allow for custom help command
    logger.info("[main.py] default help command being removed")
    bot.remove_command("help")
    # tries to loads any commands specified in the_commands into the bot

    for cog in wall_e_config.get_cogs():
        try:
            logger.info(f"[main.py] attempting to load command {cog['name']}")
            cog_file = importlib.import_module(f"{cog['path']}{cog['name']}")
            classes_that_match = inspect.getmembers(sys.modules[cog_file.__name__], inspect.isclass)
            for class_that_match in classes_that_match:
                cog_to_load = getattr(cog_file, class_that_match[0])
                if type(cog_to_load) is commands.cog.CogMeta:
                    bot.add_cog(cog_to_load(bot, wall_e_config))
                    logger.info(f"[main.py] {cog['name']} successfully loaded")
        except Exception as e:
            exception = f'{type(e).__name__}: {e}'
            logger.error(f'[main.py] Failed to load command {cog}\n{exception}')
            time.sleep(20)
            exit(1)
    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(wall_e_config.get_config_value("basic_config", "TOKEN"))
