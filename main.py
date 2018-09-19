import os
import sys
import traceback
import asyncio
import discord
import logging
import datetime
import pytz
import helper_files.testenv
from discord.ext import commands
from helper_files.logger_setup import LoggerWriter
from commands_to_load import Misc

######################
## VARIABLES TO USE ##
######################
if 'ENVIRONMENT' not in os.environ:
    print("[main.py] No environment variable \"ENVIRONMENT\" seems to exist...read the README again")
    exit(1)
ENVIRONMENT = os.environ['ENVIRONMENT']
print("[main.py] variable \"ENVIRONMENT\" is set to \""+str(ENVIRONMENT)+"\"")


BOT_LOG_CHANNEL = None
if ENVIRONMENT != 'TEST':
    if 'BOT_LOG_CHANNEL_ID' not in os.environ:
        print("[main.py] No environment variable \"BOT_LOG_CHANNEL_ID\" seems to exist...read the README again")
        exit(1)
    else:
        BOT_LOG_CHANNEL = int(os.environ['BOT_LOG_CHANNEL_ID'])
print("[main.py] variable \"BOT_LOG_CHANNEL\" is set to \""+str(BOT_LOG_CHANNEL)+"\"")

bot = commands.Bot(command_prefix='.')
FILENAME = None

# setting up path hierarchy for commands to load
commandFolder="commands_to_load."
the_commands=[commandFolder+"HealthChecks", commandFolder+"Misc", commandFolder+"RoleCommands", commandFolder+"Administration", commandFolder+"Reminders"]

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
    global FILENAME
    FILENAME="logs/"+DATE+"_wall_e"
    filehandler=logging.FileHandler("{}.log".format(FILENAME))
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

##################################################
## signals to all functions that use            ##
## "wait_until_ready" that the bot is now ready ##
## to start performing background tasks         ##
##################################################

@bot.event
async def on_ready():
    logger.info('[main.py on_ready()] Logged in as')
    logger.info('[main.py on_ready()] '+bot.user.name)
    logger.info('[main.py on_ready()] '+str(bot.user.id))
    logger.info('[main.py on_ready()] ------')
    logger.info('[main.py on_ready()] '+bot.user.name+' is now ready for commands')

##################################################################################################
## HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel():
    await bot.wait_until_ready()
    global BOT_LOG_CHANNEL
    if ENVIRONMENT == 'TEST':
        branch = os.environ['BRANCH'].lower()
        log_channel = discord.utils.get(bot.guilds[0].channels, name=branch + '_logs')
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(branch + '_logs')
        BOT_LOG_CHANNEL = log_channel.id
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
                    line="."+line
                    line=line.replace("@","[at]")
                    output=line
                    if len(line)>2000:
                        prefix="truncated output="
                        line = prefix+line
                        length = len(line)- (len(line) - 2000) #taking length of just output into account
                        length = length - len(prefix) #taking length of prefix into account
                        output=line[:length]
                    await channel.send(output)
                line = f.readline()
            await asyncio.sleep(1)

####################################################
## Function that gets called when the script cant ##
## understand the command that the user invoked   ##
####################################################
@bot.event
async def on_command_error(ctx, error):
    if helper_files.testenv.TestCog.check_test_environment(ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            fmt = '```Missing argument: {0}```'
            logger.error('[main.py on_command_error()] '+fmt.format(error.param))
            await ctx.send(fmt.format(error.param))
        else:
            for letter in str(error)[9:-14]:
                if letter != '.':
                    author = ctx.author.nick or ctx.author.name
                    #await ctx.send('Error:\n```Sorry '+author+', seems like the command \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    return

####################
## STARTING POINT ##
####################
if __name__ == "__main__":
    logger = initalizeLogger()
    logger.info("[main.py] Wall-E is starting up")

    # load the code dealing with test server interaction
    try:
        bot.load_extension('helper_files.testenv')
    except Exception as e:
        exception = '{}: {}'.format(type(e).__name__, e)
        logger.error('[main.py] Failed to load test server code testenv\n{}'.format(exception))

    ## tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info("[main.py] trying to open "+FILENAME+".log to be able to send its output to #bot_log channel")
        f = open(FILENAME+'.log', 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel())
        logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")
    except Exception as e:
        logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to following error"+str(e))

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
