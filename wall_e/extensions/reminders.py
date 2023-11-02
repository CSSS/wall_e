import asyncio
import datetime

import discord
import parsedatetime
import pytz
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from wall_e_models.models import Reminder

import django_settings
from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers, print_wall_e_exception


class Reminders(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Reminders")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[Reminders __init__()] initializing Reminders")
        self.guild = None

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "reminders_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
                "reminders_warn"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "reminders_error"
            )

    @commands.Cog.listener(name="on_ready")
    async def get_messages(self):
        """
        Background function that determines if a reminder's time has come to be sent to its channel
        :return:
        """
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info("[Reminders get_messages()] acquiring text channel for reminders.")
        reminder_chan_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            "reminders"
        )
        reminder_channel = discord.utils.get(
            self.guild.channels, id=reminder_chan_id
        )
        self.logger.debug(
            f"[Reminders get_messages()] text channel {reminder_channel} acquired."
        )
        while True:
            try:
                reminders = await Reminder.get_expired_reminders()
                for reminder in reminders:
                    reminder_message = reminder.message
                    author_id = reminder.author_id
                    self.logger.debug(f'[Reminders get_messages()] obtained the message of [{reminder_message}] for '
                                      f'author with id [{author_id}] for '
                                      f'BOT_GENERAL_CHANNEL [{reminder_chan_id}]')
                    self.logger.debug('[Reminders get_messages()] sent off '
                                      f'reminder to {author_id} about \"{reminder_message}\"')
                    e_obj = await embed(
                        self.logger,
                        reminder_channel,
                        author=bot.user,
                        description=f"This is your reminder to {reminder_message}",
                        footer='Reminder'
                    )
                    if e_obj is not False:
                        await reminder_channel.send(f'<@{author_id}>', embed=e_obj)
                    await Reminder.delete_reminder(reminder)
            except Exception as error:
                self.logger.error('[Reminders get_messages()] Ignoring exception when generating reminder:')
                print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)
            await asyncio.sleep(2)

    @commands.command(
        brief="create a reminder",
        help=(
            "Timezone assumed to be Canada/Pacific unless otherwise specified\n"
            "A list of valid timezones can be found at\n"
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones\n\n"
            "Arguments:\n"
            "---date specifier: when the reminder should be set for\n"
            "---reminder: what the reminder is actually about\n\n"
            "Example Time Formats:\n"
            ".remindmein <n> <seconds|minutes|hours|days> to <reminder>\n"
            ".remindmein <n> <day(s) after <date|tomorrow|today>> to <reminder>\n"
            ".remindmeat <time> [timezone] to [reminder>\n"
            ".remindmeon <date> [at] [time] [timezone] to <reminder>\n\n"
            "Example:\n"
            "---.remindmein 10 minutes to turn in my assignment\n"
            "---.remindmein two days after tomorrow to go to the bank\n"
            "---.remindmeat 1:15pm Canada/Eastern to video call\n"
            "---.remindmeon October 5th at 12:30pm to eat lunch\n\n"
        ),
        usage='[date specifier] to [reminder]',
        aliases=['remindmeon', 'remindmeat']
    )
    async def remindmein(self, ctx, *args):
        self.logger.info(f"[Reminders remindmein()] remindmein command detected from user {ctx.message.author}")
        parsed_time = ''
        message = ''
        user_specified_timezone = pytz.timezone(django_settings.TIME_ZONE)
        parse_time = True
        for index, value in enumerate(args):
            if parse_time:
                if value == 'to':
                    parse_time = False
                else:
                    if value in pytz.all_timezones:
                        user_specified_timezone = pytz.timezone(f"{value}")  # Set timezone if user specifies
                    parsed_time += f"{value} "
            else:
                message += f"{value} "
        if parsed_time == '':
            self.logger.debug("[Reminders remindmein()] was unable to extract a time")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=ctx.me,
                description="unable to extract a time"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        if message == '':
            self.logger.debug("[Reminders remindmein()] was unable to extract a message")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=ctx.me,
                description="unable to extract a string"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        self.logger.debug(f"[Reminders remindmein()] extracted time is {parsed_time}")
        self.logger.debug(f"[Reminders remindmein()] extracted timezone is {user_specified_timezone}")
        self.logger.debug(f"[Reminders remindmein()] extracted message is {message}")
        reminder_date, parse_status = parsedatetime.Calendar().parseDT(
            datetimeString=parsed_time,
            sourceTime=datetime.datetime.now(tz=user_specified_timezone),
            tzinfo=user_specified_timezone
        )
        if parse_status == 0:
            self.logger.debug("[Reminders remindmein()] couldn't parse the time")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=ctx.me,
                description="Could not parse time!"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
            return
        reminder_obj = Reminder(
            reminder_date_epoch=reminder_date.timestamp(), message=message,
            author_id=ctx.author.id
        )
        await Reminder.save_reminder(reminder_obj)
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            author=ctx.me,
            description=reminder_obj.get_countdown()
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj, reference=ctx.message)
            self.logger.debug("[Reminders remindmein()] reminder has been constructed and sent.")

    @commands.command(brief="Show all your active reminders and their corresponding IDs")
    async def showreminders(self, ctx):
        self.logger.info(f"[Reminders showreminders()] showreminders command detected from user {ctx.message.author}")
        try:
            reminders = ''
            reminder_objs = await Reminder.get_reminder_by_author(ctx.author.id)
            self.logger.debug(
                f"[Reminders showreminders()] retrieved all reminders belonging to user {ctx.message.author}"
            )
            for reminder_obj in reminder_objs:
                self.logger.debug(f"[Reminders showreminders()] dealing with reminder {reminder_obj}")
                time_str = datetime.datetime.fromtimestamp(
                    reminder_obj.reminder_date_epoch,
                    pytz.timezone(django_settings.TIME_ZONE)
                ).strftime("%Y %b %-d %-I:%-M:%-S %p %Z")
                reminders += f"{reminder_obj.id}\n - {time_str}\n - {reminder_obj.message}\n"
            author = ctx.author.nick or ctx.author.name
            if reminders != '':
                self.logger.debug(
                    f"[Reminders showreminders()] sent off the list of reminders to {ctx.message.author}"
                )
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title=f"Here are your reminders {author}",
                    author=ctx.me,
                    content=[["MessageID\n - Date\n - Reminder", reminders]]
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
            else:
                self.logger.debug(
                    f"[Reminders showreminders()] {ctx.message.author} didnt seem to have any reminders."
                )
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    author=ctx.me,
                    description=f"You don't seem to have any reminders {author}"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
        except Exception as error:
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=ctx.me,
                description="Something screwy seems to have happened, look at the logs for more info."
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj, reference=ctx.message)
                self.logger.error('[Reminders showreminders()] Ignoring exception when generating reminder:')
                print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)

    @commands.command(
        brief="deletes a reminder that has the specified ID",
        help=(
            'the reminder ID can be obtained by using the ".showreminders" command\n\n'
            'Arguments:\n'
            '---reminder ID: the ID of the reminder to to delete\n\n'
            'Example:\n'
            '---.deletereminder reminder ID\n\n'
        ),
        usage="reminder ID"
    )
    async def deletereminder(self, ctx, reminder_id):
        self.logger.info(
            f"[Reminders deletereminder()] deletereminder command detected from user {ctx.message.author}"
        )
        try:
            reminder = await Reminder.get_reminder_by_id(reminder_id)
            if reminder is None:
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title='Delete Reminder',
                    author=ctx.me,
                    description="ERROR\nSpecified reminder could not be found"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj, reference=ctx.message)
                    self.logger.debug("[Reminders deletereminder()] Specified reminder could not be found ")
            else:
                if reminder.author_id == ctx.message.author.id:
                    # check to make sure its the right author
                    await Reminder.delete_reminder_by_id(reminder.id)
                    self.logger.debug(f"[Reminders deletereminder()] following reminder was deleted = {reminder}")
                    e_obj = await embed(
                        self.logger,
                        ctx=ctx,
                        title='Delete Reminder',
                        author=ctx.me,
                        description=f"Following reminder has been deleted:\n{reminder.message}"
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj, reference=ctx.message)
                else:
                    e_obj = await embed(
                        self.logger,
                        ctx=ctx,
                        title='Delete Reminder',
                        author=ctx.me,
                        description="ERROR\nYou are trying to delete a reminder that is not yours"
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj, reference=ctx.message)
                        member = self.guild.get_member(reminder.author_id)
                        self.logger.debug(f"[Reminders deletereminder()] It seems that {ctx.message.author} "
                                          f"was trying to delete {member}'s reminder.")
        except Exception as error:
            self.logger.error('[Reminders.py deletereminder()] Ignoring exception when generating reminder:')
            print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)


async def setup(bot):
    await bot.add_cog(Reminders())
