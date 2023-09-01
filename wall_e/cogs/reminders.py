import asyncio
import datetime

import discord
import parsedatetime
import pytz
from discord.ext import commands
from wall_e_models.models import Reminder

import django_settings
from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers, print_wall_e_exception


class Reminders(commands.Cog):

    def __init__(self, bot, config, bot_channel_manager):
        log_info = Loggers.get_logger(logger_name="Reminders")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.config = config
        self.guild = None
        self.help_message = ''.join(self.config.get_help_json()['remindmein']['example'])
        self.bot_channel_manager = bot_channel_manager

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path, "reminders_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path, "reminders_error"
            )

    @commands.Cog.listener(name="on_ready")
    async def get_messages(self):
        """
        Background function that determines if a reminder's time has come to be sent to its channel
        :return:
        """
        while self.guild is None:
            await asyncio.sleep(2)
        reminder_chan_id = await self.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, self.config.get_config_value('basic_config', 'ENVIRONMENT'),
            "reminders"
        )
        reminder_channel = discord.utils.get(
            self.guild.channels, id=reminder_chan_id
        )
        while True:
            try:
                reminders = await Reminder.get_expired_reminders()
                for reminder in reminders:
                    reminder_message = reminder.message
                    author_id = reminder.author_id
                    self.logger.info(f'[Reminders get_messages()] obtained the message of [{reminder_message}] for '
                                     f'author with id [{author_id}] for '
                                     f'BOT_GENERAL_CHANNEL [{reminder_chan_id}]')
                    self.logger.info('[Reminders get_messages()] sent off '
                                     f'reminder to {author_id} about \"{reminder_message}\"')
                    e_obj = await embed(
                        self.logger,
                        reminder_channel,
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
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

    @commands.command(aliases=['remindmeon', 'remindmeat'])
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
            self.logger.info("[Reminders remindmein()] was unable to extract a time")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"unable to extract a time {self.help_message}"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        if message == '':
            self.logger.info("[Reminders remindmein()] was unable to extract a message")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"unable to extract a string {self.help_message}"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        self.logger.info(f"[Reminders remindmein()] extracted time is {parsed_time}")
        self.logger.info(f"[Reminders remindmein()] extracted timezone is {user_specified_timezone}")
        self.logger.info(f"[Reminders remindmein()] extracted message is {message}")
        reminder_date, parse_status = parsedatetime.Calendar().parseDT(
            datetimeString=parsed_time,
            sourceTime=datetime.datetime.now(tz=user_specified_timezone),
            tzinfo=user_specified_timezone
        )
        if parse_status == 0:
            self.logger.info("[Reminders remindmein()] couldn't parse the time")
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                title='RemindMeIn Error',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Could not parse time! {self.help_message}"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        reminder_obj = Reminder(
            reminder_date_epoch=reminder_date.timestamp(), message=message,
            author_id=ctx.author.id
        )
        await Reminder.save_reminder(reminder_obj)
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=reminder_obj.get_countdown()
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)
            self.logger.info("[Reminders remindmein()] reminder has been constructed and sent.")

    @commands.command()
    async def showreminders(self, ctx):
        self.logger.info(f"[Reminders showreminders()] showreminders command detected from user {ctx.message.author}")
        try:
            reminders = ''
            reminder_objs = await Reminder.get_reminder_by_author(ctx.author.id)
            self.logger.info(
                f"[Reminders showreminders()] retrieved all reminders belonging to user {ctx.message.author}"
            )
            for reminder_obj in reminder_objs:
                self.logger.info(f"[Reminders showreminders()] dealing with reminder {reminder_obj}")
                time_str = datetime.datetime.fromtimestamp(
                    reminder_obj.reminder_date_epoch,
                    pytz.timezone(django_settings.TIME_ZONE)
                ).strftime("%Y %b %-d %-I:%-M:%-S %p %Z")
                reminders += f"{reminder_obj.id}\n - {time_str}\n - {reminder_obj.message}\n"
            author = ctx.author.nick or ctx.author.name
            if reminders != '':
                self.logger.info(
                    f"[Reminders showreminders()] sent off the list of reminders to {ctx.message.author}"
                )
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    title=f"Here are your reminders {author}",
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    content=[["MessageID\n - Date\n - Reminder", reminders]]
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
            else:
                self.logger.info(
                    f"[Reminders showreminders()] {ctx.message.author} didnt seem to have any reminders."
                )
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"You don't seem to have any reminders {author}"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
        except Exception as error:
            e_obj = await embed(
                self.logger,
                ctx=ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Something screwy seems to have happened, look at the logs for more info."
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                self.logger.error('[Reminders showreminders()] Ignoring exception when generating reminder:')
                print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)

    @commands.command()
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
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description="ERROR\nSpecified reminder could not be found"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
                    self.logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
            else:
                if reminder.author_id == ctx.message.author.id:
                    # check to make sure its the right author
                    await Reminder.delete_reminder_by_id(reminder.id)
                    self.logger.info(f"[Reminders deletereminder()] following reminder was deleted = {reminder}")
                    e_obj = await embed(
                        self.logger,
                        ctx=ctx,
                        title='Delete Reminder',
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description=f"Following reminder has been deleted:\n{reminder.message}"
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj)
                else:
                    e_obj = await embed(
                        self.logger,
                        ctx=ctx,
                        title='Delete Reminder',
                        author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                        avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                        description="ERROR\nYou are trying to delete a reminder that is not yours"
                    )
                    if e_obj is not False:
                        await ctx.send(embed=e_obj)
                        member = self.guild.get_member(reminder.author_id)
                        self.logger.info(f"[Reminders deletereminder()] It seems that {ctx.message.author} "
                                         f"was trying to delete {member}'s reminder.")
        except Exception as error:
            self.logger.error('[Reminders.py deletereminder()] Ignoring exception when generating reminder:')
            print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)
