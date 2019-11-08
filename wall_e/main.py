import datetime
from discord.ext import commands
import importlib
import os
import psycopg2
import re
import sys
import time
import traceback

from resources.cogs.manage_cog import ManageCog
from resources.utilities.config.config import WalleConfig as config
from resources.utilities.database import setupDB, setupStatsOfCommandsDBTable
from resources.utilities.embed import embed as imported_embed
from resources.utilities.logger import initalizeLogger
from resources.utilities.log_channel import write_to_bot_log_channel

bot = commands.Bot(command_prefix='.')
config = config(os.environ['ENVIRONMENT'])


def check_test_environment(config, ctx):
    if config.get_config_value('basic_config', 'BRANCH_NAME') == 'TEST':
        if ctx.message.guild is not None and \
           ctx.channel.name != config.get_config_value('basic_config', 'BRANCH_NAME').lower():
            return False
    return True

##################################################
# signals to all functions that use            ##
# "wait_until_ready" that the bot is now ready ##
# to start performing background tasks         ##
##################################################
@bot.event
async def on_ready():
    logger.info('[main.py on_ready()] Logged in as')
    logger.info('[main.py on_ready()] ' + bot.user.name)
    logger.info('[main.py on_ready()] ' + str(bot.user.id))
    logger.info('[main.py on_ready()] ------')
    config.set_config_value("bot_profile", "BOT_NAME", bot.user.name)
    config.set_config_value("bot_profile", "BOT_AVATAR", bot.user.avatar_url)
    logger.info(
        "[main.py on_ready()] BOT_NAME initialized to {}".format(
            config.get_config_value("bot_profile", "BOT_NAME")
            )
        )
    logger.info(
        "[main.py on_ready()] BOT_AVATAR initialized to {}".format(
            config.get_config_value("bot_profile", "BOT_AVATAR")
            )
        )
    logger.info("[main.py on_ready()] {} is now ready for commands".format(bot.user.name))

####################################################
# Function that gets called when the script cant ##
# understand the command that the user invoked   ##
####################################################
@bot.event
async def on_command_error(ctx, error):
    if check_test_environment(config, ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            fmt = 'Missing argument: {0}'
            logger.error('[main.py on_command_error()] ' + fmt.format(error.param))
            eObj = await imported_embed(
                ctx,
                author=config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=fmt.format(error.param)
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
        else:
            # only prints out an error to the log if the string that was entered doesnt contain just "."
            pattern = r'[^\.]'
            if re.search(pattern, str(error)[9:-14]):
                # author = ctx.author.nick or ctx.author.name
                # await ctx.send('Error:\n```Sorry '+author+', seems like the command
                # \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                return

########################################################
# Function that gets called whenever a commmand      ##
# gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_command(ctx):
    if config.enabled("database"):
        try:
            host = config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME') + '_wall_e_db'
            dbConnectionString = (
                "dbname='" + config.get_config_value('database', 'WALL_E_DB_DBNAME') + "' "
                "user='" + config.get_config_value('database', 'WALL_E_DB_USER') + "'"
                " host='" + host + "' password"
                "='" + config.get_config_value('database', 'WALL_E_DB_PASSWORD') + "'")
            logger.info(
                "[main.py on_command()] dbConnectionString=[dbname="
                "'" + config.get_config_value('database', 'WALL_E_DB_DBNAME')
                + "' user='" + config.get_config_value('database', 'WALL_E_DB_USER') + "' "
                "host='" + host + "' password='******']")
            conn = psycopg2.connect(dbConnectionString)
            logger.info("[main.py on_command()] PostgreSQL connection established")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            index = 0
            epoch_time = int(time.time())
            now = datetime.datetime.now()
            current_year = str(now.year)
            current_month = str(now.month)
            current_day = str(now.day)
            current_hour = str(now.hour)
            channel_name = str(ctx.channel).replace("\'", "[single_quote]").strip()
            command = str(ctx.command).replace("\'", "[single_quote]").strip()
            method_of_invoke = str(ctx.invoked_with).replace("\'", "[single_quote]").strip()
            invoked_subcommand = str(ctx.invoked_subcommand).replace("\'", "[single_quote]").strip()

            # this next part is just setup to keep inserting until it finsd a primary key that is not in use
            successful = False
            while not successful:
                try:
                    sqlCommand = ("""INSERT INTO CommandStats ( \"EPOCH TIME\", YEAR, MONTH, DAY, HOUR,
                                  \"Channel Name\", Command, \"Invoked with\",
                                  "Invoked subcommand\") VALUES (""" + str(epoch_time) + """,""" + current_year
                                  + """,""" + current_month + """,""" + current_day + """,""" + current_hour
                                  + """,'""" + channel_name + """', '"""
                                  + command + """','""" + method_of_invoke + """','"""
                                  + invoked_subcommand + """');""")
                    logger.info("[main.py on_command()] sqlCommand=[" + sqlCommand + "]")
                    curs.execute(sqlCommand)
                except psycopg2.IntegrityError as e:
                    logger.error("[main.py on_command()] enountered following exception when trying to insert the "
                                 "record\n{}".format(e))
                    epoch_time += 1
                    logger.info("[main.py on_command()] incremented the epoch time to " + str(epoch_time) + " and "
                                "will try again.")
                else:
                    successful = True
            curs.close()
            conn.close()
        except Exception as e:
            logger.error("[main.py on_command()] enountered following exception when setting up PostgreSQL "
                         "connection\n{}".format(e))

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


@bot.listen()
async def on_member_join(member):
    if member is not None:
        output = "Hi, welcome to the SFU CSSS Discord Server\n"
        output += "\tWe are a group of students who live to talk about classes and nerdy stuff.\n"
        output += "\tIf you need help, please ping any of our Execs, Execs at large, or First Year Reps.\n"
        output += "\n"
        output += "\tOur general channels include some of the following:\n"
        output += "\t#off-topic, where we discuss damn near anything.\n"
        output += "\t#first-years, for students who are starting, or about to start their first year.\n"
        output += "\t#discussion, for serious non-academic discussion. (Politics et al.)\n"
        output += "\t#sfu-discussions, for all SFU related discussion.\n"
        output += "\t#projects_and_dev, for non-academic tech/dev/project discussion.\n"
        output += "\t#bot_commands_and_misc, for command testing to reduce spam on other channels.\n"
        output += "\n"
        output += "\n"
        output += "\tWe also have a smattering of course specific Academic channels.\n"
        output += "\tYou can give yourself a class role by running <.iam cmpt320> or create a new class by <.newclass"
        output += " cmpt316>\n"
        output += "\tPlease keep Academic Honesty in mind when discussing course material here.\n"
        eObj = await imported_embed(
            member,
            description=output,
            author=config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=config.get_config_value('bot_profile', 'BOT_AVATAR')
        )
        if eObj is not False:
            await member.send(embed=eObj)
            logger.info("[main.py on_member_join] embed sent to member " + str(member))

####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    logger, FILENAME = initalizeLogger()
    logger.info("[main.py] Wall-E is starting up")
    if config.enabled("database"):
        setupDB(config)
        setupStatsOfCommandsDBTable(config)
    # tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info("[main.py] trying to open " + FILENAME + ".log to be able to send its output to #bot_log channel")
        f = open(FILENAME + '.log', 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel(bot, config, f))
        logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")
    except Exception as e:
        logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                     "following error" + str(e))

    # load the code dealing with test server interaction
    try:
        bot.add_cog(ManageCog(bot, config))
    except Exception as e:
        exception = '{}: {}'.format(type(e).__name__, e)
        logger.error('[main.py] Failed to load test server code testenv\n{}'.format(exception))

    # removing default help command to allow for custom help command
    logger.info("[main.py] default help command being removed")
    bot.remove_command("help")
    # tries to loads any commands specified in the_commands into the bot

    for cog in config.get_cogs():
        commandLoaded = True
        try:
            logger.info("[main.py] attempting to load command {}".format(cog["name"]))
            cogToLoad = importlib.import_module(str(cog['path'])+str(cog["name"]))
            cogFile = getattr(cogToLoad, str(cogToLoad.getClassName()))
            bot.add_cog(cogFile(bot, config))
        except Exception as e:
            commandLoaded = False
            exception = '{}: {}'.format(type(e).__name__, e)
            logger.error('[main.py] Failed to load command {}\n{}'.format(cog, exception))
        if commandLoaded:
            logger.info("[main.py] " + cog["name"] + " successfully loaded")
    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(config.get_config_value("wall_e", "TOKEN"))
