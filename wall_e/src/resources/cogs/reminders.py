from asgiref.sync import sync_to_async
from discord.ext import commands
import discord
import logging
import asyncio
import parsedatetime
import time
import traceback
import sys

from django.conf import settings

from resources.utilities.embed import embed
import datetime
import pytz

from WalleModels.models import Reminder

logger = logging.getLogger('wall_e')


class Reminders(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot.loop.create_task(self.get_messages())

    @commands.command(aliases=['remindmeon', 'remindmeat'])
    async def remindmein(self, ctx, *args):
        logger.info("[Reminders remindmein()] remindme command detected from user {}".format(ctx.message.author))
        parsed_time = ''
        message = ''
        user_specified_timezone = pytz.timezone("Canada/Pacific")
        parse_time = True
        for index, value in enumerate(args):
            if parse_time:
                if value == 'to':
                    parse_time = False
                else:
                    if value in pytz.all_timezones:
                        user_specified_timezone = pytz.timezone(str(value))  # Set timezone if user specifies
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
                               "- Example: .remindmeon October 5th at 12:30pm to eat lunch\n")
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
        logger.info("[Reminders remindmein()] extracted timezone is {}".format(user_specified_timezone))
        logger.info("[Reminders remindmein()] extracted message is {}".format(message))
        reminder_date, parse_status = parsedatetime.Calendar().parseDT(
            datetimeString=time_until,
            sourceTime=datetime.datetime.now(tz=user_specified_timezone),
            tzinfo=user_specified_timezone
        )
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
        date_to_be_reminded_in_epoch_format = (
                reminder_date - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
        ).total_seconds()
        reminder_obj = Reminder(
            reminder_date_epoch=date_to_be_reminded_in_epoch_format, message=message,
            author_id=ctx.author.id, author_name=ctx.message.author,
            message_id=ctx.message.id
        )
        await sync_to_async(save_reminder, thread_sensitive=True)(reminder_obj)
        expire_seconds = int(date_to_be_reminded_in_epoch_format - time.time())
        e_obj = await embed(
            ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=convert_seconds_to_countdown(expire_seconds)
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)
            logger.info("[Reminders remindmein()] reminder has been contructed and sent.")

    @commands.command()
    async def showreminders(self, ctx):
        logger.info("[Reminders showreminders()] remindme command detected from user {}".format(ctx.message.author))
        try:
            reminders = ''
            logger.info("[Reminders showreminders()] retrieved all reminders belonging to user "
                        + str(ctx.message.author))
            reminders_that_belong_to_author = await sync_to_async(
                get_reminder_synchronously_that_belong_to_author, thread_sensitive=True
            )(ctx.author.id)
            for reminder_obj in reminders_that_belong_to_author:
                logger.info("[Reminders showreminders()] dealing with reminder [{}]".format(reminder_obj))
                time_str = datetime.datetime.fromtimestamp(reminder_obj.reminder_date_epoch,
                                                           pytz.timezone('America/Vancouver'))
                time_str = time_str.strftime("%Y %b %-d %-I:%-M:%-S %p %Z")
                reminders += f"{reminder_obj.message_id}\n - {time_str}\n - {reminder_obj.message}\n"
            author = ctx.author.nick or ctx.author.name
            if reminders != '':
                logger.info("[Reminders showreminders()] sent off the list of reminders to "
                            + str(ctx.message.author))
                e_obj = await embed(
                    ctx,
                    title="Here are your reminders {}".format(author),
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    content=[["MessageID\n - Date\n - Reminder", reminders]]
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
    async def show_all_reminders(self, ctx):
        try:
            reminders = ''
            logger.info("[Reminders showreminders()] retrieved all reminders belonging to user "
                        + str(ctx.message.author))
            all_reminders = await sync_to_async(
                get_all_reminder_synchronously, thread_sensitive=True
            )()
            for reminder_obj in all_reminders:
                logger.info("[Reminders showreminders()] dealing with reminder [{}]".format(reminder_obj))
                time_str = datetime.datetime.fromtimestamp(reminder_obj.reminder_date_epoch,
                                                           pytz.timezone('America/Vancouver'))
                time_str = time_str.strftime("%Y %b %-d %-I:%-M:%-S %p %Z")
                reminders += (
                    f"{reminder_obj.message_id}\n - Date: {time_str}\n - Reminder: {reminder_obj.message}"
                    f"\n - Author: <@{reminder_obj.author_id}>"
                )
            author = ctx.author.nick or ctx.author.name
            if reminders != '':
                logger.info(f"[Reminders showreminders()] sent off the list of reminders to {ctx.message.author}")
                e_obj = await embed(
                    ctx,
                    title="Reminders",
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    content=[["Current Reminders", reminders]]
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
                reminder = Reminder.objects.all().filter(message_id=message_id)
                if reminder is None:
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
                    if str(reminder[4]) == str(ctx.message.author):
                        # check to make sure its the right author
                        reminder.delete()
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
            reminder_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')
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
                    name='{}_bot_channel'.format(self.config.get_config_value('basic_config', 'BRANCH_NAME').lower())
                )
                if reminder_chan is None:
                    reminder_chan = await self.bot.guilds[0].create_text_channel(
                        '{}_bot_channel'.format(self.config.get_config_value('basic_config', 'BRANCH_NAME'))
                    )
                    reminder_channel_id = reminder_chan.id
                    if reminder_channel_id is None:
                        logger.info(
                            "[Reminders get_messages()] the channel designated for reminders [{}_bot_channel] in {} "
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
                reminder_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')
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
            try:
                reminders = await sync_to_async(get_reminders_syncronously, thread_sensitive=True)()
                for reminder in reminders:
                    reminder_message = reminder.message
                    author_id = reminder.author_id
                    logger.info('[Reminders get_message()] obtained the message of [{}] for '
                                'author with id [{}] for '
                                'BOT_GENERAL_CHANNEL [{}]'.format(reminder_message, author_id, reminder_channel_id))
                    logger.info('[Reminders get_message()] sent off '
                                'reminder to {} about \"{}\"'.format(author_id, reminder_message))
                    e_obj = await embed(
                        reminder_channel,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="This is your reminder to {}".format(reminder_message),
                        footer='Reminder'
                    )
                    await sync_to_async(delete_reminder_syncronously, thread_sensitive=True)(reminder)
                    if e_obj is not False:
                        pass
                        await reminder_channel.send('<@{}>'.format(author_id), embed=e_obj)
            except Exception as error:
                logger.error('[Reminders get_message()] Ignoring exception when generating reminder:')
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await asyncio.sleep(2)


def get_reminders_syncronously():
    today_date = datetime.datetime.now(tz=pytz.timezone(str(settings.TIME_ZONE)))
    start_of_epoch = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
    epoch_time_zone_user_timezone = (today_date - start_of_epoch).total_seconds()
    return list(Reminder.objects.all().filter(reminder_date_epoch__lte=epoch_time_zone_user_timezone))


def delete_reminder_syncronously(reminder_to_delete):
    reminder_to_delete.delete()


def get_reminder_synchronously_that_belong_to_author(author_id):
    return list(Reminder.objects.all().filter(author_id=author_id).order_by('reminder_date_epoch'))


def get_all_reminder_synchronously():
    return list(Reminder.objects.all().order_by('reminder_date_epoch'))


def save_reminder(reminder_to_save):
    reminder_to_save.save()


def convert_seconds_to_countdown(seconds):
    day = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    message = "Reminder set for "
    if day > 0:
        message += f" {day} days"
    if hour > 0:
        message += f" {hour} hours"
    if minutes > 0:
        message += f" {minutes} minutes"
    if seconds > 0:
        message += f" {seconds} seconds"
    return f"{message} from now"
