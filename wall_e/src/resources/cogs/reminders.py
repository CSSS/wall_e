from discord.ext import commands
import discord
# import json
import logging
import asyncio
import parsedatetime
import time
from time import mktime
# import helper_files.testenv
import traceback
import sys
from resources.utilities.embed import embed
import psycopg2
# import os
import datetime
logger = logging.getLogger('wall_e')


def getClassName():
    return "Reminders"


class Reminders(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

        # setting up database connection
        try:
            host = self.config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME') + '_wall_e_db'
            dbConnectionString = (
                "dbname='{}' user='{}' host='{}' password='{}'".format(
                    self.config.get_config_value('database', 'WALL_E_DB_DBNAME'),
                    self.config.get_config_value('database', 'WALL_E_DB_USER'),
                    host,
                    self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')
                )
            )
            logger.info(
                "[Reminders __init__] dbConnectionString=[dbname='{}' user='{}' host='{}' password='******']".format(
                    self.config.get_config_value('database', 'WALL_E_DB_DBNAME'),
                    self.config.get_config_value('database', 'WALL_E_DB_USER'),
                    host
                )
            )
            conn = psycopg2.connect(dbConnectionString)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.curs = conn.cursor()
            self.curs.execute("CREATE TABLE IF NOT EXISTS Reminders ( reminder_id BIGSERIAL  PRIMARY KEY, "
                              "reminder_date timestamp DEFAULT now() + interval '1' year, message varchar(2000) "
                              "DEFAULT 'INVALID', author_id varchar(500) DEFAULT 'INVALID', author_name varchar(500)"
                              " DEFAULT 'INVALID', message_id varchar(200) DEFAULT 'INVALID');")
            self.bot.loop.create_task(self.get_messages())
            logger.info("[Reminders __init__] PostgreSQL connection established")
        except Exception as e:
            logger.error("[Reminders __init__] enountered following exception when setting up PostgreSQL "
                         "connection\n{}".format(e))

    @commands.command()
    async def remindmein(self, ctx, *args):
        logger.info("[Reminders remindmein()] remindme command detected from user " + str(ctx.message.author))
        parsedTime = ''
        message = ''
        parseTime = True
        for index, value in enumerate(args):
            if parseTime:
                if value == 'to':
                    parseTime = False
                else:
                    parsedTime += str(value) + " "
            else:
                message += str(value) + " "
        how_to_call_command = ("\nPlease call command like so:\nremindmein <time|minutes|hours|days> to <what to "
                               "remind you about>\nExample: \".remindmein 10 minutes to turn in my assignment\"")
        if parsedTime == '':
            logger.info("[Reminders remindmein()] was unable to extract a time")
            eObj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="unable to extract a time" + str(how_to_call_command)
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        if message == '':
            logger.info("[Reminders remindmein()] was unable to extract a message")
            eObj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="unable to extract a string" + str(how_to_call_command)
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        timeUntil = str(parsedTime)
        logger.info("[Reminders remindmein()] extracted time is " + str(timeUntil))
        logger.info("[Reminders remindmein()] extracted message is " + str(message))
        time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
        if parse_status == 0:
            logger.info("[Reminders remindmein()] couldn't parse the time")
            eObj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Could not parse time!" + how_to_call_command
            )
            if eObj is not False:
                await ctx.send(embed=eObj)
            return
        expire_seconds = int(mktime(time_struct) - time.time())
        dt = datetime.datetime.now()
        b = dt + datetime.timedelta(seconds=expire_seconds)  # days, seconds, then other fields.
        sqlCommand = ("INSERT INTO Reminders (  reminder_date, message, author_id, author_name, message_id) VALUES "
                      "(TIMESTAMP '" + str(b) + "', '" + message + "', '" + str(ctx.author.id) + "', '"
                      + str(ctx.message.author) + "',  '" + str(ctx.message.id) + "');")
        logger.info("[Reminders remindmein()] sqlCommand=[" + sqlCommand + "]")
        self.curs.execute(sqlCommand)
        fmt = 'Reminder set for {0} seconds from now'
        eObj = await embed(
            ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=fmt.format(expire_seconds)
        )
        if eObj is not False:
            await ctx.send(embed=eObj)
            logger.info("[Reminders remindmein()] reminder has been contructed and sent.")

    @commands.command()
    async def showreminders(self, ctx):
        logger.info("[Reminders showreminders()] remindme command detected from user " + str(ctx.message.author))
        if self.curs is not None:
            try:
                reminders = ''
                sqlCommand = "SELECT * FROM Reminders WHERE author_id = '" + str(ctx.author.id) + "';"
                self.curs.execute(sqlCommand)
                logger.info("[Reminders showreminders()] retrieved all reminders belonging to user "
                            + str(ctx.message.author))
                for row in self.curs.fetchall():
                    logger.info("[Reminders showreminders()] dealing with reminder [" + str(row) + "]")
                    reminders += str(row[5]) + "\t\t\t" + str(row[2]) + "\n"
                author = ctx.author.nick or ctx.author.name
                if reminders != '':
                    logger.info("[Reminders showreminders()] sent off the list of reminders to "
                                + str(ctx.message.author))
                    eObj = await embed(
                        ctx,
                        title="Here are you reminders " + author,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        content=[["MessageID\t\t\t\t\t\t\tReminder", reminders]]
                    )
                    if eObj is not False:
                        await ctx.send(embed=eObj)
                else:
                    logger.info("[Reminders showreminders()] " + str(ctx.message.author) + " didnt seem to have any "
                                "reminders.")
                    eObj = await embed(
                        ctx,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="You don't seem to have any reminders " + author
                    )
                    if eObj is not False:
                        await ctx.send(embed=eObj)
            except Exception as error:
                eObj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description="Something screwy seems to have happened, look at the logs for more info."
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)
                    logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.command()
    async def deletereminder(self, ctx, messageId):
        logger.info("[Reminders deletereminder()] deletereminder command detected from user "
                    + str(ctx.message.author))
        try:
            if self.curs is not None:
                sqlCommand = "SELECT * FROM Reminders WHERE message_id = '" + str(messageId) + "';"
                self.curs.execute(sqlCommand)
                result = self.curs.fetchone()
                if result is None:
                    eObj = await embed(
                        ctx,
                        title='Delete Reminder',
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="ERROR\nSpecified reminder could not be found"
                    )
                    if eObj is not False:
                        await ctx.send(embed=eObj)
                        logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
                else:
                    if str(result[4]) == str(ctx.message.author):
                        # check to make sure its the right author
                        sqlCommand = "DELETE FROM Reminders WHERE message_id = '" + str(messageId) + "';"
                        self.curs.execute(sqlCommand)
                        logger.info("[Reminders deletereminder()] following reminder was deleted = " + str(result))
                        eObj = await embed(
                            ctx,
                            title='Delete Reminder',
                            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                            description="Following reminder has been deleted:\n" + str(result[2])
                        )
                        if eObj is not False:
                            await ctx.send(embed=eObj)
                    else:
                        eObj = await embed(
                            ctx,
                            title='Delete Reminder',
                            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                            description="ERROR\nYou are trying to delete a reminder that is not yours"
                        )
                        if eObj is not False:
                            await ctx.send(embed=eObj)
                            logger.info("[Reminders deletereminder()] It seems that  " + str(ctx.message.author)
                                        + " was trying to delete " + str(result[4]) + "'s reminder.")
        except Exception as error:
            logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################
# Background function that determines ##
# if a reminder's time has come       ##
# to be sent to its channel           ##
#########################################
    async def get_messages(self):
        await self.bot.wait_until_ready()
        REMINDER_CHANNEL_ID = None
        # determines the channel to send the reminder on
        try:
            reminder_channel_name = self.config.get_config_value('basic_config', 'REMINDER_CHANNEL')
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'PRODUCTION':
                logger.info(
                    "[Reminders get_messages()] environment is =[{}]".format(
                        self.config.get_config_value('basic_config', 'ENVIRONMENT')
                    )
                )
                reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name=reminder_channel_name)
                if reminder_chan is None:
                    logger.info("[Reminders get_messages()] reminder channel does not exist in PRODUCTION.")
                    reminder_chan = await self.bot.guilds[0].create_text_channel(reminder_channel_name)
                    REMINDER_CHANNEL_ID = reminder_chan.id
                    if REMINDER_CHANNEL_ID is None:
                        logger.info("[Reminders get_messages()] the channel designated for reminders "
                                    "[{}] in PRODUCTION does not exist and I was unable to create "
                                    "it, exiting now....".format(reminder_channel_name))
                        exit(1)
                    logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""
                                + str(REMINDER_CHANNEL_ID) + "\"")
                else:
                    logger.info("[Reminders get_messages()] reminder channel exists in PRODUCTION and was detected.")
                    REMINDER_CHANNEL_ID = reminder_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
                logger.info(
                    "[Reminders get_messages()] branch is =[{}]".format(
                        self.config.get_config_value('basic_config', 'BRANCH_NAME')
                    )
                )
                reminder_chan = discord.utils.get(
                    self.bot.guilds[0].channels,
                    name=self.config.get_config_value('basic_config', 'BRANCH_NAME').lower() + '_reminders'
                )
                if reminder_chan is None:
                    reminder_chan = await self.bot.guilds[0].create_text_channel(
                        self.config.get_config_value('basic_config', 'BRANCH_NAME') + '_reminders'
                    )
                    REMINDER_CHANNEL_ID = reminder_chan.id
                    if REMINDER_CHANNEL_ID is None:
                        logger.info(
                            "[Reminders get_messages()] the channel designated for reminders [{}_reminders] in {} "
                            "does not exist and I was unable to create it, exiting now....".format(
                                self.config.get_config_value('basic_config', 'BRANCH_NAME'),
                                self.config.get_config_value('basic_config', 'BRANCH_NAME')
                            )
                        )
                        exit(1)
                    logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""
                                + str(REMINDER_CHANNEL_ID) + "\"")
                else:
                    logger.info(
                        "[Reminders get_messages()] reminder channel exists in {} and was "
                        "detected.".format(
                            self.config.get_config_value('basic_config', 'BRANCH_NAME')
                        )
                    )
                    REMINDER_CHANNEL_ID = reminder_chan.id
            else:
                reminder_chan = discord.utils.get(
                    self.bot.guilds[0].channels,
                    name=self.config.get_config_value('basic_config', 'ENVIRONMENT').lower() + '_reminders'
                )
                if reminder_chan is None:
                    reminder_chan = await self.bot.guilds[0].create_text_channel('localhost_reminders')
                    REMINDER_CHANNEL_ID = reminder_chan.id
                    if REMINDER_CHANNEL_ID is None:
                        logger.info("[Reminders get_messages()] the channel designated for reminders "
                                    "[localhost_reminders] does not exist and I was unable to create it, "
                                    "exiting now....")
                        exit(1)
                    logger.info("[Reminders get_messages()] variable \"REMINDER_CHANNEL_ID\" is set to \""
                                + str(REMINDER_CHANNEL_ID) + "\"")
                else:
                    logger.info("[Reminders get_messages()] reminder channel exists and was detected.")
                    REMINDER_CHANNEL_ID = reminder_chan.id
        except Exception as e:
            logger.error("[Reminders get_messages()] enountered following exception when connecting to reminder "
                         "channel\n{}".format(e))
        reminder_channel = self.bot.get_channel(REMINDER_CHANNEL_ID)  # channel ID goes here
        while True:
            dt = datetime.datetime.now()
            try:
                self.curs.execute("SELECT * FROM Reminders where reminder_date <= TIMESTAMP '" + str(dt) + "';")
                for row in self.curs.fetchall():
                    reminder_message = row[2]
                    author_id = row[3]
                    logger.info('[Misc.py get_message()] obtained the message of [' + str(reminder_message) + '] for '
                                'author with id [' + str(author_id) + '] for REMINDER_CHANNEL ['
                                + str(REMINDER_CHANNEL_ID) + ']')
                    logger.info('[Misc.py get_message()] sent off reminder to ' + str(author_id) + " about \""
                                + reminder_message + "\"")
                    eObj = await embed(
                        reminder_channel,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="This is your reminder to " + reminder_message,
                        footer='Reminder'
                    )
                    self.curs.execute("DELETE FROM Reminders WHERE reminder_id = " + str(row[0]) + ";")
                    if eObj is not False:
                        await reminder_channel.send('<@' + author_id + '>', embed=eObj)
            except Exception as error:
                logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await asyncio.sleep(2)
