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
import helper_files.settings as settings
from helper_files.embed import embed
import re
import json
import wolframalpha


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

print('[main.py] loading cog names from json file')
with open('commands_to_load/cogs.json') as c:
    cogs = json.load(c)
cogs = cogs['cogs']

print("[main.py] loading Wolfram Alpha API Environment Variable")
if 'WOLFRAMAPI' not in os.environ:
    print("[main.py] No environment variable \"WOLFRAMAPI\" seems to exist...read the README again")
    exit(1)
wolframAPI = os.environ['WOLFRAMAPI']
wolframClient = wolframalpha.Client(wolframAPI)

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

    settings.BOT_NAME = bot.user.name
    settings.BOT_AVATAR = bot.user.avatar_url
    logger.info('[main.py on_ready()] BOT_NAME initialized to '+str(settings.BOT_NAME)+ ' in settings.py')
    logger.info('[main.py on_ready()] BOT_AVATAR initialized to '+str(settings.BOT_AVATAR)+ ' in settings.py')

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
                    line=line.replace("@","[at]")
                    if line[0] == ' ':
                        line = "." + line
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
            fmt = 'Missing argument: {0}'
            logger.error('[main.py on_command_error()] '+fmt.format(error.param))
            eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(error.param))
            await ctx.send(embed=eObj)
        else:
            #only prints out an error to the log if the string that was entered doesnt contain just "."
            pattern = r'[^\.]'
            if re.search(pattern, str(error)[9:-14]):
                    author = ctx.author.nick or ctx.author.name
                    #await ctx.send('Error:\n```Sorry '+author+', seems like the command \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    return

########################################################
## Function that gets called whenever a commmand      ##
## gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_command(ctx):
    stat_file = open("logs/stats_of_commands.csv", 'a+')

    index=0
    argument=''
    for arg in ctx.args:
        if index > 1:
            if ',' in arg:
                arg = arg.replace(',', '[comma]')
            argument += arg+' '
        index+=1

    author=str(ctx.message.author)
    if ',' in author:
        author=author.replace(",","[comma]")

    now = datetime.datetime.now()
    stat_file.write(str(now.year)+', '+str(now.month)+', '+str(now.day)+', '+str(now.hour)+', '+str(str(ctx.channel.id))+", "+str(str(ctx.channel))+", "+str(author)+", "+str(ctx.command)+", "+str(argument)+", "+str(ctx.invoked_with)+", "+str(ctx.invoked_subcommand)+"\n")

@bot.listen()
async def on_member_join(member):

    if member is not None:
        from helper_files.embed import embed as imported_embed

        output="Hi, welcome to the SFU CSSS Discord Server's"+str(os.environ['BRANCH'])+" branch.\n"
        output+="\tWe are a group of students who live to talk about classes and nerdy stuff.\n"
        output+="\tIf you need help, please ping any of our Execs, Execs at large, or First Year Reps.\n"
        output+="\n"
        output+="\tOur general channels include some of the following:\n"
        output+="\t#off-topic, where we discuss damn near anything.\n"
        output+="\t#first-years, for students who are starting, or about to start their first year.\n"
        output+="\t#discussion, for serious non-academic discussion. (Politics et al.)\n"
        output+="\t#sfu-discussions, for all SFU related discussion.\n"
        output+="\t#projects_and_dev, for non-academic tech/dev/project discussion.\n"
        output+="\t#bot_commands_and_misc, for command testing to reduce spam on other channels.\n"
        output+="\n"
        output+="\n"
        output+="\tWe also have a smattering of course specific Academic channels.\n"
        output+="\tYou can give yourself a class role by running <.iam cmpt320> or create a new class by <.newclass cmpt316>\n"
        output+="\tPlease keep Academic Honesty in mind when discussing course material here.\n"

        eObj = imported_embed(title="Welcome to the SFU CSSS's Discord Channel", author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=output)
        await member.send(embed=eObj,content=None)
        logger.info("[main.py on_member_join] embed sent to member "+str(member))

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
    for cog in cogs:
        commandLoaded=True
        try:
            logger.info("[main.py] attempting to load command "+ cog["name"])
            bot.load_extension(cog["folder"] + '.' + cog["name"])
        except Exception as e:
            commandLoaded=False
            exception = '{}: {}'.format(type(e).__name__, e)
            logger.error('[main.py] Failed to load command {}\n{}'.format(cog["name"], exception))
        if commandLoaded:
            logger.info("[main.py] " + cog["name"] + " successfully loaded")

    from pathlib import Path
    my_file = Path("logs/stats_of_commands.csv")
    if my_file.is_file():
        print("[main.py] stats_of_commands.csv already exist")
    else:
        print("[main.py] stats_of_commands.csv didn't exist, creating it now....")
        stat_file = open("logs/stats_of_commands.csv", 'a+')
        stat_file.write("Year, Month, Date, Hour, Channel Name, Channel ID, Author, Command, Argument, Invoked_with, Invoked_subcommand\n")
        stat_file.close()

    ##final step, running the bot with the passed in environment TOKEN variable
    TOKEN = os.environ['TOKEN']
    bot.run(TOKEN)
