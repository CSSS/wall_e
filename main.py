import sys
import traceback
import asyncio
import discord
import logging
import datetime
import pytz
from resources.utilities.config.config import WalleConfig as config
from resources.cogs import testenv
from resources.utilities.logger_setup import LoggerWriter
from resources.utilities.embed import embed as imported_embed
import re
import os
import importlib
from discord.ext import commands
import time
import aiohttp
bot = commands.Bot(command_prefix='.')
config = config(os.environ['ENVIRONMENT'])

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
    createLogFile(formatter, logger)
    return logger


def createLogFile(formatter, logger):
    DATE = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y_%m_%d_%H_%M_%S")
    global FILENAME
    FILENAME = "logs/" + DATE + "_wall_e"
    filehandler = logging.FileHandler("{}.log".format(FILENAME))
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)


###############################
# SETUP DATABASE CONNECTION ##
###############################
def setupDB():
    try:
        host = None
        env = config.get_config_value("wall_e", "ENVIRONMENT")
        compose_project_name = config.get_config_value("wall_e", "COMPOSE_PROJECT_NAME")
        postgres_db_dbname = config.get_config_value("database", "POSTGRES_DB_DBNAME")
        postgres_db_user = config.get_config_value("database", "POSTGRES_DB_USER")
        postgres_password = config.get_config_value("database", "POSTGRES_PASSWORD")
        wall_e_db_dbname = config.get_config_value("database", "WALL_E_DB_DBNAME")
        wall_e_db_user = config.get_config_value("database", "WALL_E_DB_USER")
        wall_e_db_password =config.get_config_value("database", "WALL_E_DB_PASSWORD")

        if 'localhost' == env:
            host = '127.0.0.1'
        else:
            host = compose_project_name + '_wall_e_db'
        dbConnectionString = ("dbname='" + postgres_db_dbname + "' user='" + postgres_db_user + "' "
                              "host='" + host + "' password='" + postgres_password + "'")
        logger.info("[main.py setupDB] Postgres User dbConnectionString=[dbname='" + postgres_db_dbname
                    + "' user='" + postgres_db_user + "' host='" + host + "' password='*****']")
        postgresConn = psycopg2.connect(dbConnectionString)
        logger.info("[main.py setupDB] PostgreSQL connection established")
        postgresConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        postgresCurs = postgresConn.cursor()
        # these two parts is using a complicated DO statement because apparently postgres does not have an
        # "if not exist" clause for roles or databases, only tables moreover, this is done to localhost and not any
        # other environment cause with the TEST guild, the databases are always brand new fresh with each time the
        # script get launched
        if 'localhost' == env or'PRODUCTION' == env:
            # aquired from https://stackoverflow.com/a/8099557/7734535
            sqlQuery = """DO
            $do$
            BEGIN
            IF NOT EXISTS (
            SELECT                       -- SELECT list can stay empty for this
            FROM   pg_catalog.pg_roles
            WHERE  rolname = '""" + wall_e_db_user + """') THEN
            CREATE ROLE """ + wall_e_db_user + """ WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN
             NOREPLICATION NOBYPASSRLS ENCRYPTED PASSWORD '""" + wall_e_db_password + """';
            END IF;
            END
            $do$;"""
            postgresCurs.execute(sqlQuery)
        else:
            postgresCurs.execute("CREATE ROLE " + wall_e_db_user + " WITH NOSUPERUSER INHERIT "
                                 "NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS ENCRYPTED "
                                 "PASSWORD '" + wall_e_db_password + "';")
        logger.info("[main.py setupDB] " + wall_e_db_user + " role created")
        if 'localhost' == env or 'PRODUCTION' == env:
            sqlQuery = """SELECT datname from pg_database"""
            postgresCurs.execute(sqlQuery)
            results = postgresCurs.fetchall()
            # fetchAll returns  [('postgres',), ('template0',), ('template1',), ('csss_discord_db',)]
            # which the below line converts to  ['postgres', 'template0', 'template1', 'csss_discord_db']
            results = [x for xs in results for x in xs]
            if wall_e_db_dbname not in results:
                postgresCurs.execute("CREATE DATABASE " + wall_e_db_dbname + " WITH OWNER"
                                     " " + wall_e_db_user + " TEMPLATE = template0;")
                logger.info("[main.py setupDB] " + wall_e_db_dbname + " database created")
            else:
                logger.info("[main.py setupDB] " + wall_e_db_dbname + " database already exists")
        else:
            postgresCurs.execute("CREATE DATABASE " + wall_e_db_dbname + " WITH OWNER"
                                 " " + wall_e_db_user + " TEMPLATE = template0;")
            logger.info("[main.py setupDB] " + wall_e_db_dbname + " database created")
        # this section exists cause of this backup.sql that I had exported from an instance of a Postgres with
        # which I had created the csss_discord_db
        # https://github.com/CSSS/wall_e/blob/implement_postgres/helper_files/backup.sql#L31
        dbConnectionString = ("dbname='" + wall_e_db_dbname + "' user='" + postgres_db_user + "'"
                              " host='" + host + "' password='" + postgres_password + "'")
        logger.info("[main.py setupDB] Wall_e User dbConnectionString=[dbname='" + wall_e_db_dbname + "'"
                    " user='" + postgres_db_user + "' host='" + host + "' password='*****']")
        walleConn = psycopg2.connect(dbConnectionString)
        logger.info("[main.py setupDB] PostgreSQL connection established")
        walleConn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        walleCurs = walleConn.cursor()
        walleCurs.execute("SET statement_timeout = 0;")
        walleCurs.execute("SET default_transaction_read_only = off;")
        walleCurs.execute("SET lock_timeout = 0;")
        walleCurs.execute("SET idle_in_transaction_session_timeout = 0;")
        walleCurs.execute("SET client_encoding = 'UTF8';")
        walleCurs.execute("SET standard_conforming_strings = on;")
        walleCurs.execute("SELECT pg_catalog.set_config('search_path', '', false);")
        walleCurs.execute("SET check_function_bodies = false;")
        walleCurs.execute("SET client_min_messages = warning;")
        walleCurs.execute("SET row_security = off;")
        walleCurs.execute("CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;")
        walleCurs.execute("COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';")
    except Exception as e:
        logger.error("[main.py setupDB] enountered following exception when setting up PostgreSQL "
                     "connection\n{}".format(e))

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
    config.set_config_value("wall_e", "BOT_NAME", bot.user.name)
    config.set_config_value("wall_e", "BOT_AVATAR", bot.user.avatar_url)
    logger.info('[main.py on_ready()] BOT_NAME initialized to ' + str(config.get_config_value("wall_e", "BOT_NAME")))
    logger.info('[main.py on_ready()] BOT_AVATAR initialized to ' + str(config.get_config_value("wall_e", "BOT_AVATAR")))
    logger.info('[main.py on_ready()] ' + bot.user.name + ' is now ready for commands')


##################################################################################################
# HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel():
    await bot.wait_until_ready()
    # only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
    # Production is a permanant channel so that it can be persistent. As for localhost,
    # the idea was that this removes a dependence on the user to make the channel and shifts that
    # responsibility to the script itself. thereby requiring less effort from the user
    bot_log_channel = None
    env = config.get_config_value("wall_e", "ENVIRONMENT")
    branch_name = config.get_config_value("wall_e", "BRANCH_NAME")
    log_channel_name = config.get_config_value("wall_e", "BOT_LOG_CHANNEL")
    if (env == "LOCALHOST" or env == "PRODUCTION") and log_channel_name == 'NONE':
        print("no name detected for bot log channel in settings....exit")


    if env == "LOCALHOST":
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
        bot_log_channel = log_channel.id
    elif env == "DEV":
        log_channel_name = branch_name.lower() + '_logs'
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
        bot_log_channel = log_channel.id
    elif env == "PRODUCTION":
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        bot_log_channel = log_channel.id

    channel = bot.get_channel(bot_log_channel)  # channel ID goes here
    if channel is None:
        logger.error("[main.py write_to_bot_log_channel] could not retrieve the bot_log channel with id "
                     + str(bot_log_channel) + " . Please investigate further")
    else:
        logger.info("[main.py write_to_bot_log_channel] bot_log channel with id " + str(bot_log_channel)
                    + " successfully retrieved.")
        while not bot.is_closed():
            f.flush()
            line = f.readline()
            while line:
                if line.strip() != "":
                    # this was done so that no one gets accidentally pinged from the bot log channel
                    line = line.replace("@", "[at]")
                    if line[0] == ' ':
                        line = "." + line
                    output = line
                    # done because discord has a character limit of 2000 for each message
                    # so what basically happens is it first tries to send the full message, then if it cant, it
                    # breaks it down into 2000 sizes messages and send them individually
                    try:
                        await channel.send(output)
                    except (aiohttp.ClientError, discord.errors.HTTPException):
                        finished = False
                        firstIndex, lastIndex = 0, 2000
                        while not finished:
                            await channel.send(output[firstIndex:lastIndex])
                            firstIndex = lastIndex
                            lastIndex += 2000
                            if len(output[firstIndex:lastIndex]) == 0:
                                finished = True
                    except Exception as exc:
                        exc_str = '{}: {}'.format(type(exc).__name__, exc)
                        logger.error('[main.py write_to_bot_log_channel] write to channel failed\n{}'.format(exc_str))
                line = f.readline()
            await asyncio.sleep(1)

####################################################
# Function that gets called when the script cant ##
# understand the command that the user invoked   ##
####################################################
@bot.event
async def on_command_error(ctx, error):
    if testenv.TestCog.check_test_environment(ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            fmt = 'Missing argument: {0}'
            logger.error('[main.py on_command_error()] ' + fmt.format(error.param))
            eObj = await imported_embed(ctx, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                                        description=fmt.format(error.param))
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


def setupStatsOfCommandsDBTable():
    try:
        host = None
        if 'localhost' == settings.ENVIRONMENT:
            host = '127.0.0.1'
        else:
            host = settings.COMPOSE_PROJECT_NAME + '_wall_e_db'
        dbConnectionString = ("dbname='" + settings.WALL_E_DB_DBNAME + "' user='" + settings.WALL_E_DB_USER + "'"
                              " host='" + host + "' password='" + settings.WALL_E_DB_PASSWORD + "'")
        logger.info("[main.py setupStatsOfCommandsDBTable()] dbConnectionString=[dbname='"
                    + settings.WALL_E_DB_DBNAME + "' user='" + settings.WALL_E_DB_USER + "' host='" + host
                    + "' password='******']")
        conn = psycopg2.connect(dbConnectionString)
        logger.info("[main.py setupStatsOfCommandsDBTable()] PostgreSQL connection established")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        curs = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS CommandStats ( \"EPOCH TIME\" BIGINT  PRIMARY KEY, YEAR BIGINT, "
                     "MONTH BIGINT, DAY BIGINT, HOUR BIGINT, \"Channel ID\" BIGINT, \"Channel Name\" varchar(2000), "
                     "Author varchar(2000), Command varchar(2000), Argument varchar(2000), \"Invoked with\" "
                     "varchar(2000), \"Invoked subcommand\"  varchar(2000));")
        logger.info("[main.py setupStatsOfCommandsDBTable()] CommandStats database table created")
    except Exception as e:
        logger.error("[main.py setupStatsOfCommandsDBTable()] enountered following exception when setting up "
                     "PostgreSQL connection\n{}".format(e))

########################################################
# Function that gets called whenever a commmand      ##
# gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_command(ctx):
    if testenv.TestCog.check_test_environment(ctx) and settings.ENVIRONMENT != 'localhost_noDB':
        try:
            host = None
            if 'localhost' == settings.ENVIRONMENT:
                host = '127.0.0.1'
            else:
                host = settings.COMPOSE_PROJECT_NAME + '_wall_e_db'
            dbConnectionString = ("dbname='" + settings.WALL_E_DB_DBNAME + "' user='" + settings.WALL_E_DB_USER + "'"
                                  " host='" + host + "' password='" + settings.WALL_E_DB_PASSWORD + "'")
            logger.info("[main.py on_command()] dbConnectionString=[dbname='" + settings.WALL_E_DB_DBNAME
                        + "' user='" + settings.WALL_E_DB_USER + "' host='" + host + "' password='******']")
            conn = psycopg2.connect(dbConnectionString)
            logger.info("[main.py on_command()] PostgreSQL connection established")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
            index = 0
            argument = ''
            for arg in ctx.args:
                if index > 1:
                    argument += arg + ' '
                index += 1
            epoch_time = int(time.time())
            now = datetime.datetime.now()
            current_year = str(now.year)
            current_month = str(now.month)
            current_day = str(now.day)
            current_hour = str(now.hour)
            channel_id = str(ctx.channel.id)
            channel_name = str(ctx.channel).replace("\'", "[single_quote]").strip()
            if ctx.guild.get_member(ctx.message.author.id).name.isalnum():
                author = str(ctx.message.author).replace("\'", "[single_quote]").strip()
            else:
                author = "<" + str(ctx.message.author.id).replace("\'", "[single_quote]").strip() + ">"
            command = str(ctx.command).replace("\'", "[single_quote]").strip()
            argument = (
                    str(argument).replace("\'", "[single_quote]").strip() if command != "embed"
                    else "redacted due to large size")
            method_of_invoke = str(ctx.invoked_with).replace("\'", "[single_quote]").strip()
            invoked_subcommand = str(ctx.invoked_subcommand).replace("\'", "[single_quote]").strip()

            # this next part is just setup to keep inserting until it finsd a primary key that is not in use
            successful = False
            while not successful:
                try:
                    sqlCommand = ("""INSERT INTO CommandStats ( \"EPOCH TIME\", YEAR, MONTH, DAY, HOUR,
                                  "Channel ID\", \"Channel Name\", Author, Command, Argument, \"Invoked with\",
                                  "Invoked subcommand\") VALUES (""" + str(epoch_time) + """,""" + current_year
                                  + """,""" + current_month + """,""" + current_day + """,""" + current_hour
                                  + """,""" + channel_id + """,'""" + channel_name + """','""" + author + """', '"""
                                  + command + """','""" + argument + """','""" + method_of_invoke + """','"""
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
        eObj = await imported_embed(member, description=output, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR)
        if eObj is not False:
            await member.send(embed=eObj)
            logger.info("[main.py on_member_join] embed sent to member " + str(member))

####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    FILENAME = None
    logger = initalizeLogger()
    logger.info("[main.py] Wall-E is starting up")
    if config.get_config_value("database", "enabled") == '1':
        setupDB()
        setupStatsOfCommandsDBTable()
    # tries to open log file in prep for write_to_bot_log_channel function
    try:
        logger.info("[main.py] trying to open " + FILENAME + ".log to be able to send its output to #bot_log channel")
        f = open(FILENAME + '.log', 'r')
        f.seek(0)
        bot.loop.create_task(write_to_bot_log_channel())
        logger.info("[main.py] log file successfully opened and connection to bot_log channel has been made")
    except Exception as e:
        logger.error("[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                     "following error" + str(e))
    # load the code dealing with test server interaction
    try:
        bot.load_extension('resources.cogs.testenv')
    except Exception as e:
        exception = '{}: {}'.format(type(e).__name__, e)
        logger.error('[main.py] Failed to load test server code testenv\n{}'.format(exception))
    # removing default help command to allow for custom help command
    logger.info("[main.py] default help command being removed")
    bot.remove_command("help")
    # tries to loads any commands specified in the_commands into the bot

    #cogs = __import('resources')
    for cog in config.get_cogs():
        commandLoaded = True
        try:
            logger.info("[main.py] attempting to load command {}".format(cog["name"]))
            admin = importlib.import_module( str(cog['path'])+str(cog["name"]))
            attr = getattr(admin, str(cog["name"]))
            bot.add_cog(attr(bot))
            #bot.add_cog(class_3(bot))
            #bot.load_extension(class_)
        except Exception as e:
            commandLoaded = False
            exception = '{}: {}'.format(type(e).__name__, e)
            logger.error('[main.py] Failed to load command {}\n{}'.format(cog, exception))
        if commandLoaded:
            logger.info("[main.py] " + cog["name"] + " successfully loaded")
    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(config.get_config_value("wall_e", "TOKEN"))
