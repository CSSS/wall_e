from discord.ext import commands
import importlib
import os
import inspect
import sys
from resources.cogs.manage_cog import ManageCog
from resources.utilities.config.config import WallEConfig
from resources.utilities.database import setup_database, setup_stats_of_command_database_table
from resources.utilities.embed import embed as imported_embed
from resources.utilities.logger_setup import initialize_logger
from resources.utilities.log_channel import write_to_bot_log_channel
from discord import Intents
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
    logger.info('[main.py on_ready()] {}'.format(bot.user.name))
    logger.info('[main.py on_ready()] {}'.format(str(bot.user.id)))
    logger.info('[main.py on_ready()] ------')
    WallEConfig.set_config_value("bot_profile", "BOT_NAME", bot.user.name)
    WallEConfig.set_config_value("bot_profile", "BOT_AVATAR", bot.user.avatar_url)
    logger.info(
        "[main.py on_ready()] BOT_NAME initialized to {}".format(
            WallEConfig.get_config_value("bot_profile", "BOT_NAME")
            )
        )
    logger.info(
        "[main.py on_ready()] BOT_AVATAR initialized to {}".format(
            WallEConfig.get_config_value("bot_profile", "BOT_AVATAR")
            )
        )
    logger.info("[main.py on_ready()] {} is now ready for commands".format(bot.user.name))


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
    logger, FILENAME = initialize_logger()
    WallEConfig = WallEConfig(os.environ['ENVIRONMENT'])

    logger.info("[main.py] Wall-E is starting up")
    if WallEConfig.enabled("database", option="DB_ENABLED"):
        setup_database(WallEConfig)
        setup_stats_of_command_database_table(WallEConfig)
    # tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info("[main.py] trying to open {}.log to be able to send "
                    "its output to #bot_log channel".format(FILENAME))
        f = open('{}.log'.format(FILENAME), 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel(bot, WallEConfig, f))
        logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")
    except Exception as e:
        logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                     "following error{}".format(e))

    # load the code dealing with test server interaction
    try:
        bot.add_cog(ManageCog(bot, WallEConfig))
    except Exception as e:
        exception = '{}: {}'.format(type(e).__name__, e)
        logger.error('[main.py] Failed to load test server code testenv\n{}'.format(exception))

    # removing default help command to allow for custom help command
    logger.info("[main.py] default help command being removed")
    bot.remove_command("help")
    # tries to loads any commands specified in the_commands into the bot

    for cog in WallEConfig.get_cogs():
        try:
            logger.info("[main.py] attempting to load command {}".format(cog["name"]))
            cog_file = importlib.import_module(str(cog['path'])+str(cog["name"]))
            cog_class_name = inspect.getmembers(sys.modules[cog_file.__name__], inspect.isclass)[0][0]
            cog_to_load = getattr(cog_file, cog_class_name)
            bot.add_cog(cog_to_load(bot, WallEConfig))
            logger.info("[main.py] {} successfully loaded".format(cog["name"]))
        except Exception as e:
            exception = '{}: {}'.format(type(e).__name__, e)
            logger.error('[main.py] Failed to load command {}\n{}'.format(cog, exception))
    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(WallEConfig.get_config_value("basic_config", "TOKEN"))
