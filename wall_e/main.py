import asyncio
import datetime
import importlib
import inspect
import logging
import os
import re
import sys
import time

import discord
import django
from discord import Intents
from discord.ext import commands
from django.core.wsgi import get_wsgi_application

from utilities.bot_channel_manager import BotChannelManager, wall_e_category_name
from utilities.config.config import WallEConfig
from utilities.embed import embed as imported_embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers, print_wall_e_exception, barrier_logging_level, WalleDebugStreamHandler
from utilities.slash_command_checks import command_in_correct_test_guild_channel

log_info = Loggers.get_logger(logger_name="sys")
sys_debug_log_file_absolute_path = log_info[1]
sys_error_log_file_absolute_path = log_info[2]

discordpy_log_info = Loggers.get_logger(logger_name="discord.py")
discordpy_logger = discordpy_log_info[0]
discordpy_debug_log_file_absolute_path = discordpy_log_info[1]
discordpy_error_log_file_absolute_path = discordpy_log_info[2]

log_info = Loggers.get_logger(logger_name="wall_e")

logger = log_info[0]
wall_e_debug_log_file_absolute_path = log_info[1]
wall_e_error_log_file_absolute_path = log_info[2]

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")
django.setup()

wall_e_config = WallEConfig(os.environ['basic_config__ENVIRONMENT'])

application = get_wsgi_application()

intents = Intents.all()


class WalleBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=intents)
        self.bot_channel_manager = BotChannelManager(wall_e_config, self)
        self.uploading = False

    async def setup_hook(self) -> None:
        # removing default help command to allow for custom help command
        logger.info("[main.py] default help command being removed")
        self.remove_command("help")

        await bot.add_custom_cog()
        # tries to load any commands specified in the_commands into the bot
        logger.info("[main.py] commands cleared and synced")
        await super().setup_hook()

    async def remove_custom_cog(self, folder: str, module_name: str):
        cog_module = importlib.import_module(folder + module_name)
        class_names = inspect.getmembers(sys.modules[cog_module.__name__], inspect.isclass)
        for class_name in class_names:
            if class_name[0].lower() == module_name.lower():
                cog_class_to_load = class_name[1]
                cog_class_has_no_slash_commands = (
                    (not hasattr(cog_class_to_load, "__cog_app_commands__")) or
                    len(cog_class_to_load.__cog_app_commands__) == 0
                )  # adding this in cause
                # discord is just way to buggy to reliably unload and reload a slash command at this time
                if type(cog_class_to_load) is commands.cog.CogMeta and cog_class_has_no_slash_commands:
                    await self.remove_cog(class_name[0])

    async def add_custom_cog(self, module_path_and_name: str = None):
        guild = discord.Object(id=int(wall_e_config.get_config_value("basic_config", "GUILD_ID")))
        adding_all_cogs = module_path_and_name is None
        cog_unloaded = False
        for cog in wall_e_config.get_cogs():
            if cog_unloaded:
                break
            try:
                if adding_all_cogs or module_path_and_name == f"{cog['path']}{cog['name']}":
                    cog_module = importlib.import_module(f"{cog['path']}{cog['name']}")
                    classes_that_match = inspect.getmembers(sys.modules[cog_module.__name__], inspect.isclass)
                    for class_that_match in classes_that_match:
                        cog_class_to_load = getattr(cog_module, class_that_match[0])
                        if type(cog_class_to_load) is commands.cog.CogMeta:
                            logger.info(f"[main.py] attempting to load cog {cog['name']}")
                            # the below piece of logic will not work well in the test guild if there
                            # are multiple PRs being worked on at the same time that have different
                            # slash command as there is no way to avoid a conflict. I tried to fix this
                            # by having the bot in multiple guilds, one for each PR, but there is no way to
                            # know till too late [when the bot is already logged in] the GUILD ID of the TEST
                            # guild the bot is being deployed to, which it needs to know what guild to add the
                            # cogs to.
                            await self.add_cog(
                                cog_class_to_load(self, wall_e_config, self.bot_channel_manager),
                                guild=guild
                            )
                            logger.info(f"[main.py] {cog['name']} successfully loaded")
                            if not adding_all_cogs:
                                cog_unloaded = True
                                break
            except Exception as err:
                exception = f'{type(err).__name__}: {err}'
                logger.error(f'[main.py] Failed to load command {cog}\n{exception}')
                if adding_all_cogs:
                    time.sleep(20)
                    exit(1)


bot = WalleBot()


##################################################
# signals to all functions that use            ##
# "wait_until_ready" that the bot is now ready ##
# to start performing background tasks         ##
##################################################
@bot.event
async def on_ready():
    bot_guild = bot.guilds[0]
    # tries to open log file in prep for write_to_bot_log_channel function
    if bot.uploading is False and wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
        try:
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, sys_debug_log_file_absolute_path, "sys_debug"
            )
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, sys_error_log_file_absolute_path, "sys_error"
            )
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, wall_e_debug_log_file_absolute_path, "wall_e_debug"
            )
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, wall_e_error_log_file_absolute_path, "wall_e_error"
            )
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, discordpy_debug_log_file_absolute_path, "discordpy_debug"
            )
            await start_file_uploading(
                logger, bot_guild, bot, wall_e_config, discordpy_error_log_file_absolute_path, "discordpy_error"
            )
            bot.uploading = True
        except Exception as e:
            raise Exception(
                "[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                f"following error {e}")
    logger.info('[main.py on_ready()] Logged in as')
    logger.info(f'[main.py on_ready()] {bot.user.name}')
    logger.info(f'[main.py on_ready()] {bot.user.id}')
    logger.info('[main.py on_ready()] ------')
    wall_e_config.set_config_value("bot_profile", "BOT_NAME", bot.user.name)
    wall_e_config.set_config_value("bot_profile", "BOT_AVATAR", bot.user.avatar.url)
    logger.info(
        "[main.py on_ready()] BOT_NAME initialized to"
        f" {wall_e_config.get_config_value('bot_profile', 'BOT_NAME')}"
    )
    logger.info(
        "[main.py on_ready()] BOT_AVATAR initialized to "
        f"{wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR')}"

    )
    logger.info(f"[main.py on_ready()] {bot.user.name} is now ready for commands")


########################################################
# Function that gets called any input or output from ##
# the script					     ##
########################################################
@bot.event
async def on_message(message):
    if message.guild is None and message.author != bot.user:
        em = await imported_embed(
            logger,
            ctx=message.author,
            description="[welcome to the machine](https://platform.openai.com/login?launch)"
        )
        if em is not None:
            await message.author.send(embed=em)
    else:
        await bot.process_commands(message)


########################################################
# Function that gets called whenever a commmand      ##
# gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, cmd: discord.app_commands.commands.Command):
    database_enabled = wall_e_config.enabled("database_config", option="ENABLED")
    correct_channel = await command_in_correct_test_guild_channel(wall_e_config, interaction)
    if correct_channel and database_enabled:
        from wall_e_models.models import CommandStat
        await CommandStat.save_command_stat(CommandStat(
            epoch_time=datetime.datetime.now().timestamp(), channel_name=interaction.channel.name,
            command=interaction.command.name, invoked_with=cmd.qualified_name,
            invoked_subcommand=None
        ))


@bot.listen()
async def on_raw_reaction_add(reaction):
    """
    Adding a listener method that allows the Bot_manager to delete a stack trace in an error text channel if
     a Bot_manager has fixed the error in the stack trace. Just a nice way to keep a clean error text channel and a
     quick visual indicator of whether an error has been fixed

    :param reaction:
    :return:
    """
    guild = bot.guilds[0]
    stack_trace_has_been_tackled = reaction.emoji.name == '👍🏿'

    users_roles = [role.name for role in discord.utils.get(guild.members, id=reaction.user_id).roles]
    reaction_is_from_bot_manager = "Bot_manager" in users_roles

    channel_with_reaction = discord.utils.get(guild.channels, id=reaction.channel_id)
    reaction_not_sent_in_regular_channel = channel_with_reaction is None
    if reaction_not_sent_in_regular_channel:
        return
    channel_category = channel_with_reaction.category
    if channel_category is None:
        return
    text_channel_is_in_log_channel_category = channel_category.name == wall_e_category_name

    error_log_channel = channel_with_reaction.name[-6:] == '_error'
    valid_error_channel = (
        stack_trace_has_been_tackled and reaction_is_from_bot_manager and
        text_channel_is_in_log_channel_category and error_log_channel
    )
    if not valid_error_channel:
        return
    traceback_message_index = -1
    channel = channel_with_reaction
    last_message_checked = None

    # will try to find the message that contains the Traceback string as that's the most reliable way to
    # detect the beginning of a stack trace in a channel
    while traceback_message_index == -1:
        messages = [message async for message in channel.history(limit=100, before=last_message_checked)]
        iteration = 0
        if len(messages) > 0:
            while traceback_message_index == -1 and iteration < len(messages):
                if "Traceback (most recent call last):" in messages[iteration].content:
                    traceback_message_index = iteration
                iteration += 1
        else:
            # could not find the original traceback message string
            # will just clear the whole channel instead I guess
            traceback_message_index = None

        if traceback_message_index == -1:
            # traceback message not found but there is more potential message to look through
            last_message_checked = messages[len(messages)-1]
        elif traceback_message_index is None:
            # whole channel has to be cleared
            last_message_checked = None
        else:
            # traceback message found, will now try to find the message before it as that message is needed
            # for the "after" parameter when getting the whole stacktrace
            if len(messages) == traceback_message_index+1:

                # seems the message before the traceback message was not retrieved in the messages list, so
                # another call needs to be made just for that message
                previous_messages = [
                    message async for message in
                    channel.history(limit=1, before=messages[traceback_message_index])
                ]
                # either a previous message exists and was obtained, indicating that there
                # is a suitable message for the "after" cursor or there is no previous
                # message, so "None" should be used
                last_message_checked = previous_messages[0] if len(previous_messages) > 0 else None
            else:
                # if the code was lucky, the message right before the Traceback is in the list of
                # messages that were already retrieved so the code just need to look at the next
                # message in the list for the "after" parameter
                last_message_checked = messages[traceback_message_index+1]
    messages_to_delete = [
        message async for message in channel.history(after=last_message_checked, oldest_first=False)
    ]
    await channel.delete_messages(messages_to_delete, reason="issue fixed")
    message = (
        'Last' +
        (f" {len(messages_to_delete)} messages" if len(messages_to_delete) > 1 else " message") +
        " deleted"
    )
    e_obj = await imported_embed(
        logger,
        ctx=channel,
        author=wall_e_config.get_config_value('bot_profile', 'BOT_NAME'),
        avatar=wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR'),
        description=message,
    )
    if e_obj is not False:
        message = await channel.send(embed=e_obj)
        await asyncio.sleep(10)
        await message.delete()


####################################################
# Function that gets called when the script cant ##
# understand the command that the user invoked   ##
####################################################
@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error):
    correct_channel = await command_in_correct_test_guild_channel(wall_e_config, interaction)
    if correct_channel:
        if isinstance(error, commands.MissingRequiredArgument):
            logger.error(f'[main.py on_command_error()] Missing argument: {error.param}')
            e_obj = await imported_embed(
                logger,
                interaction=interaction,
                author=wall_e_config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Missing argument: {error.param}"
            )
            if e_obj is not False:
                await interaction.response.send_message(embed=e_obj)
        elif isinstance(error, commands.errors.CommandNotFound):
            return
        else:
            # only prints out an error to the log if the string that was entered doesnt contain just "."
            pattern = r'[^\.]'
            if re.search(pattern, f"{error}"[9:-14]):
                if type(error) is discord.ext.commands.errors.CheckFailure:
                    raise Exception(
                        f"[main.py on_command_error()] user {interaction.user} "
                        "probably tried to access a command they arent supposed to"
                    )
                else:
                    try:
                        print_wall_e_exception(
                            error, error.__traceback__, error_logger=error.command.binding.logger.error
                        )
                    except Exception:
                        print_wall_e_exception(error, error.__traceback__, error_logger=logger.error)
                    return


class DiscordPyDebugStreamHandler(logging.StreamHandler):
    def __init__(self):
        self.debug_handler = [
            handler for handler in discordpy_logger.handlers if type(handler) == WalleDebugStreamHandler
        ][0]
        self.error_handler = [
            handler for handler in discordpy_logger.handlers if type(handler) == logging.StreamHandler
        ][0]
        super(DiscordPyDebugStreamHandler, self).__init__()

    def emit(self, record):
        if record.levelno < barrier_logging_level:
            self.debug_handler.emit(record)
        else:
            self.error_handler.emit(record)


####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    logger.info("[main.py] Wall-E is starting up")

    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(wall_e_config.get_config_value("basic_config", "TOKEN"), log_handler=DiscordPyDebugStreamHandler())
