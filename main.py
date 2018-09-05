import os
import sys
import time
import traceback
import asyncio
import json
import redis
import parsedatetime
import discord
import logging
import datetime
import pytz
from time import mktime
from discord.ext import commands
from logger_setup import LoggerWriter

######################
## VARIABLES TO USE ##
######################
BOT_LOG_CHANNEL = 478776321808269322
BOT_USER_ID = 482394461993828353
bot = commands.Bot(command_prefix='.')

# setting up path hierarchy for commands to load
commandFolder="commands_to_load."
the_commands=[commandFolder+"HealthChecks", commandFolder+"Misc", commandFolder+"RoleCommands", commandFolder+"Administration"]

##################
## LOGGING SETUP ##
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
    createLogFile(formatter, logger)
    return logger

def createLogFile(formatter,logger):
    DATE=datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y_%m_%d_%H_%M_%S")
    FILENAME="wall_e"
    filehandler=logging.FileHandler("{}.log".format(FILENAME))
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

#######################
## NEEDS DESCRIPTION ##
#######################
@bot.event
async def on_ready():
    logger.info('[main.py on_ready()] Logged in as')
    logger.info('[main.py on_ready()] '+bot.user.name)
    logger.info('[main.py on_ready()] '+str(bot.user.id))
    logger.info('[main.py on_ready()] ------')
    bot.loop.create_task(get_messages())

##################################################################################################
## HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel():
    await bot.wait_until_ready()
    channel = bot.get_channel(BOT_LOG_CHANNEL) # channel ID goes here
    if channel is None:
        logger.error("[main.py write_to_bot_log_channel] could not retrieve the bot_log channel with id " +str(BOT_LOG_CHANNEL) +" . Please investigate further")
    else:
        logger.info("[main.py write_to_bot_log_channel] bot_log channel with id " +str(BOT_LOG_CHANNEL) +" successfully retrieved.")
        while not bot.is_closed():
            f.flush()
            line = f.readline()
            while line:
                if line.strip() != "":
                    await channel.send(line)
                line = f.readline()
            await asyncio.sleep(1)

#######################
## NEEDS DESCRIPTION ##
#######################
async def get_messages():
    await bot.wait_until_ready()
    while True:
        message = message_subscriber.get_message()
        if message is not None and message['type'] == 'message':
            try:
                cid_mid_dct = json.loads(message['data'])
                chan = bot.get_channel(cid_mid_dct['cid'])
                msg = await chan.get_message(cid_mid_dct['mid'])
                ctx = await bot.get_context(msg)
                if ctx.valid:
                    fmt = '<@{0}> ```{1}```'
                    await ctx.send(fmt.format(ctx.message.author.id, ctx.message.content))
            except Exception as error:
                logger.error('[main.py get_message()] Ignoring exception when generating reminder:')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await asyncio.sleep(2)

#######################
## NEEDS DESCRIPTION ##
#######################
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        fmt = '```Missing argument: {0}```'
        await ctx.send(fmt.format(error.param))
    else:
        logger.error('[main.py on_command_error()] Ignoring exception in command {}:'.format(ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

####################
## STARTING POINT ##
####################
if __name__ == "__main__":
    logger = initalizeLogger()
    logger.info("[main.py] Wall-E is starting up")

    ## tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info("[main.py] trying to open wall_e.log to be able to send its output to #bot_log channel")
        f = open('wall_e.log', 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel())
        logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")        
    except Exception as e:
        logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to following error"+str(e))

    #setting up database connection
    try:
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        message_subscriber = r.pubsub(ignore_subscribe_messages=True)
        message_subscriber.subscribe('__keyevent@0__:expired')
        logger.info("[main.py] redis connection established")
    except Exception as e:
        logger.error("[main.py] enountered following exception when setting up redis connection:"+e)

    #removing default help command to allow for custom help command
    logger.info("[main.py] default help command being removed")
    bot.remove_command("help")

    ## tries to loads any commands specified in the_commands into the bot
    for com in the_commands:
        commandLoaded=True
        try:
            logger.info("[main.py] attempting to load command "+com)
            bot.load_extension(com)
        except Exception as e:
            commandLoaded=False
            exception = '{}: {}'.format(type(e).__name__, e)
            logger.error('[main.py] Failed to load command {}\n{}'.format(com, exception))
        if commandLoaded:
            logger.info("[main.py] "+com+" successfully loaded")

    ##final step, running the bot with the passed in environment TOKEN variable
    TOKEN = os.environ['TOKEN']
    bot.run(TOKEN)