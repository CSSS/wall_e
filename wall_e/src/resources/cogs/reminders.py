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
import pytz
logger = logging.getLogger('wall_e')


class Reminders(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

        # setting up database connection
        try:
            host = '{}_wall_e_db'.format(self.config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME'))
            db_connection_string = (
                "dbname='{}' user='{}' host='{}'".format(
                    self.config.get_config_value('database', 'WALL_E_DB_DBNAME'),
                    self.config.get_config_value('database', 'WALL_E_DB_USER'),
                    host)
            )
            logger.info("[Reminders __init__] db_connection_string=[{}]".format(db_connection_string))
            conn = psycopg2.connect(
                "{}  password='{}'".format(
                    db_connection_string, self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')
                )
            )
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

    @commands.command(aliases=['remindmeon', 'remindmeat'])
    async def remindmein(self, ctx, *args):
        logger.info("[Reminders remindmein()] remindme command detected from user {}".format(ctx.message.author))
        parsed_time = ''
        message = ''
        # Bot's default timezone; if running from another timezone (eg: Canada/Eastern), change accordingly
        user_timezone = pytz.timezone("Canada/Pacific")
        parse_time = True
        for index, value in enumerate(args):
            if parse_time:
                if value == 'to':
                    parse_time = False
                else:
                    if value in pytz.all_timezones:
                        user_timezone = pytz.timezone(str(value))  # Set timezone if user specifies
                    parsed_time += "{} ".format(value)
            else:
                message += "{} ".format(value)
        how_to_call_command = ("\n"
                               "Please call command like so:\n\n"
                               "remindmein <time format> to <what to remind you about>\n"
                               "remindmeon <time format> to <what to remind you about>\n"
                               "remindmeat <time format> to <what to remind you about>\n\n"
                               "Timezone assumed to be Canada/Pacific unless otherwise specified\n"
                               "A list of valid timezones can be found at\n"
                               "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones\n\n"
                               "Example Time Formats:\n"
                               "[n] [seconds|minutes|hours]\n"
                               "- Example: .remindmein 10 minutes to turn in my assignment\n\n"
                               "[n] [day(s) after [date|tomorrow|today]]\n"
                               "- Example: .remindmein two days after tomorrow to go to the bank\n\n"
                               "[time] [timezone]?\n"
                               "- Example: .remindmeat 1:15pm Canada/Eastern to video call\n\n"
                               "[date] [at]? [time] [timezone]?\n"
                               "- Example: .remindmeon Oct 5th at 12:30pm to eat lunch\n")
        if parsed_time == '':
            logger.info("[Reminders remindmein()] was unable to extract a time")
            e_obj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="unable to extract a time {}".format(how_to_call_command)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        if message == '':
            logger.info("[Reminders remindmein()] was unable to extract a message")
            e_obj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="unable to extract a string {}".format(how_to_call_command)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        time_until = str(parsed_time)
        logger.info("[Reminders remindmein()] extracted time is {}".format(time_until))
        logger.info("[Reminders remindmein()] extracted timezone is {}".format(user_timezone))
        logger.info("[Reminders remindmein()] extracted message is {}".format(message))
        current_time = datetime.datetime.now(tz=user_timezone)
        time_struct, parse_status = parsedatetime.Calendar().parseDT(
                datetimeString=time_until, sourceTime=current_time, tzinfo=user_timezone)
        if parse_status == 0:
            logger.info("[Reminders remindmein()] couldn't parse the time")
            e_obj = await embed(
                ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Could not parse time! {}".format(how_to_call_command)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        time_struct = time_struct.utctimetuple()  # Server runs in UTC, so time has to be converted
        expire_seconds = int(mktime(time_struct) - time.time())
        dt = datetime.datetime.now(tz=pytz.utc)  # Note that datetime.utcnow() returns naive datetime
        b = dt + datetime.timedelta(seconds=expire_seconds)  # days, seconds, then other fields.
        sql_command = (
            "INSERT INTO Reminders (  reminder_date, message, author_id, author_name, message_id) VALUES "
            "(TIMESTAMP '{}', '{}', '{}', '{}',  '{}');".format(
                b,
                message,
                ctx.author.id,
                ctx.message.author,
                ctx.message.id
            )
        )
        logger.info("[Reminders remindmein()] sql_command=[{}]".format(sql_command))
        self.curs.execute(sql_command)
        fmt = 'Reminder set for {0} seconds from now'
        e_obj = await embed(
            ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=fmt.format(expire_seconds)
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)
            logger.info("[Reminders remindmein()] reminder has been contructed and sent.")

    @commands.command()
    async def showreminders(self, ctx):
        logger.info("[Reminders showreminders()] remindme command detected from user {}".format(ctx.message.author))
        if self.curs is not None:
            try:
                reminders = ''
                sql_command = "SELECT * FROM Reminders WHERE author_id = '{}';".format(ctx.author.id)
                self.curs.execute(sql_command)
                logger.info("[Reminders showreminders()] retrieved all reminders belonging to user "
                            + str(ctx.message.author))
                for row in self.curs.fetchall():
                    logger.info("[Reminders showreminders()] dealing with reminder [{}]".format(row))
                    reminders += "{}\t\t\t{}\n".format(row[5], row[2])
                author = ctx.author.nick or ctx.author.name
                if reminders != '':
                    logger.info("[Reminders showreminders()] sent off the list of reminders to "
                                + str(ctx.message.author))
                    e_obj = await embed(
                        ctx,
                        title="Here are your reminders {}".format(author),
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        content=[["MessageID\t\t\t\t\t\t\tReminder", reminders]]
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj)
                else:
                    logger.info(
                        "[Reminders showreminders()] {} didnt seem to have any reminders.".format(
                            ctx.message.author
                        )
                    )
                    e_obj = await embed(
                        ctx,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="You don't seem to have any reminders {}".format(author)
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj)
            except Exception as error:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description="Something screwy seems to have happened, look at the logs for more info."
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
                    logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.command()
    async def deletereminder(self, ctx, message_id):
        logger.info("[Reminders deletereminder()] deletereminder command detected from user "
                    + str(ctx.message.author))
        try:
            if self.curs is not None:
                sql_command = "SELECT * FROM Reminders WHERE message_id = '{}';".format(message_id)
                self.curs.execute(sql_command)
                result = self.curs.fetchone()
                if result is None:
                    e_obj = await embed(
                        ctx,
                        title='Delete Reminder',
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="ERROR\nSpecified reminder could not be found"
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj)
                        logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
                else:
                    if str(result[4]) == str(ctx.message.author):
                        # check to make sure its the right author
                        sql_command = "DELETE FROM Reminders WHERE message_id = '{}';".format(message_id)
                        self.curs.execute(sql_command)
                        logger.info("[Reminders deletereminder()] following reminder was deleted = {}".format(result))
                        e_obj = await embed(
                            ctx,
                            title='Delete Reminder',
                            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                            description="Following reminder has been deleted:\n{}".format(result[2])
                        )
                        if e_obj is not False:
                            await ctx.send(embed=e_obj)
                    else:
                        e_obj = await embed(
                            ctx,
                            title='Delete Reminder',
                            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                            description="ERROR\nYou are trying to delete a reminder that is not yours"
                        )
                        if e_obj is not False:
                            await ctx.send(embed=e_obj)
                            logger.info("[Reminders deletereminder()] It seems that {} "
                                        "was trying to delete {}'s reminder.".format(ctx.message.author, result[4]))
        except Exception as error:
            logger.error('[Reminders.py deletereminder()] Ignoring exception when generating reminder:')
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################
# Background function that determines ##
# if a reminder's time has come       ##
# to be sent to its channel           ##
#########################################
    async def get_messages(self):
        await self.bot.wait_until_ready()
        reminder_channel_id = None
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
                    reminder_channel_id = reminder_chan.id
                    if reminder_channel_id is None:
                        logger.info("[Reminders get_messages()] the channel designated for reminders "
                                    "[{}] in PRODUCTION does not exist and I was unable to create "
                                    "it, exiting now....".format(reminder_channel_name))
                        exit(1)
                    logger.info("[Reminders get_messages()] variable "
                                "\"reminder_channel_id\" is set to \"{}\"".format(reminder_channel_id))
                else:
                    logger.info("[Reminders get_messages()] reminder channel exists in PRODUCTION and was detected.")
                    reminder_channel_id = reminder_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
                logger.info(
                    "[Reminders get_messages()] branch is =[{}]".format(
                        self.config.get_config_value('basic_config', 'BRANCH_NAME')
                    )
                )
                reminder_chan = discord.utils.get(
                    self.bot.guilds[0].channels,
                    name='{}_reminders'.format(self.config.get_config_value('basic_config', 'BRANCH_NAME').lower())
                )
                if reminder_chan is None:
                    reminder_chan = await self.bot.guilds[0].create_text_channel(
                         '{}_reminders'.format(self.config.get_config_value('basic_config', 'BRANCH_NAME'))
                    )
                    reminder_channel_id = reminder_chan.id
                    if reminder_channel_id is None:
                        logger.info(
                            "[Reminders get_messages()] the channel designated for reminders [{}_reminders] in {} "
                            "does not exist and I was unable to create it, exiting now....".format(
                                self.config.get_config_value('basic_config', 'BRANCH_NAME'),
                                self.config.get_config_value('basic_config', 'BRANCH_NAME')
                            )
                        )
                        exit(1)
                    logger.info("[Reminders get_messages()] variable "
                                "\"reminder_channel_id\" is set to \"{}\"".format(reminder_channel_id))
                else:
                    logger.info(
                        "[Reminders get_messages()] reminder channel exists in {} and was "
                        "detected.".format(
                            self.config.get_config_value('basic_config', 'BRANCH_NAME')
                        )
                    )
                    reminder_channel_id = reminder_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
                reminder_channel_name = self.config.get_config_value('basic_config', 'REMINDER_CHANNEL')
                logger.info(
                    "[Reminders get_messages()] environment is =[{}]".format(
                        self.config.get_config_value('basic_config', 'ENVIRONMENT')
                    )
                )
                reminder_chan = discord.utils.get(self.bot.guilds[0].channels, name=reminder_channel_name)
                if (reminder_chan is None):
                    logger.info("[Remindes get_messages()] reminder channel does not exist in local dev.")
                    reminder_chan = await self.bot.guilds[0].create_text_channel(reminder_channel_name)
                    reminder_channel_id = reminder_chan.id
                    if reminder_channel_id is None:
                        logger.info("[Reminders get_messages()] the channel designated for reminders "
                                    "[{}] in local dev does not exist and I was unable to create it "
                                    "it, exiting now.....".format(reminder_channel_name))
                        exit(1)
                    logger.info("[Reminders get_messages()] variables "
                                "\"reminder_channel_id\" is set to \"{}\"".format(reminder_channel_id))
                else:
                    logger.info("[Reminders get_messages()] reminder channel exists in local dev and was detected.")
                    reminder_channel_id = reminder_chan.id
        except Exception as e:
            logger.error("[Reminders get_messages()] enountered following exception when connecting to reminder "
                         "channel\n{}".format(e))
        reminder_channel = self.bot.get_channel(reminder_channel_id)  # channel ID goes here
        while True:
            dt = datetime.datetime.now()
            try:
                self.curs.execute("SELECT * FROM Reminders where reminder_date <= TIMESTAMP '{}';".format(dt))
                for row in self.curs.fetchall():
                    reminder_message = row[2]
                    author_id = row[3]
                    logger.info('[Reminders get_message()] obtained the message of [{}] for '
                                'author with id [{}] for '
                                'REMINDER_CHANNEL [{}]'.format(reminder_message, author_id, reminder_channel_id))
                    logger.info('[Reminders get_message()] sent off '
                                'reminder to {} about \"{}\"'.format(author_id, reminder_message))
                    e_obj = await embed(
                        reminder_channel,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="This is your reminder to {}".format(reminder_message),
                        footer='Reminder'
                    )
                    self.curs.execute("DELETE FROM Reminders WHERE reminder_id = {};".format(row[0]))
                    if e_obj is not False:
                        await reminder_channel.send('<@{}>'.format(author_id), embed=e_obj)
            except Exception as error:
                logger.error('[Reminders get_message()] Ignoring exception when generating reminder:')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await asyncio.sleep(2)
