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
from discord import Intents, Interaction
from discord.ext import commands
from django.core.wsgi import get_wsgi_application

from utilities.bot_channel_manager import BotChannelManager, wall_e_category_name
from utilities.config.config import WallEConfig
from utilities.embed import embed as imported_embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers, print_wall_e_exception

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

# needs to be after django.setup()
from cogs.help_commands import EmbedHelpCommand # noqa E402
from wall_e_models.models import HelpMessage # noqa E402

intents = Intents.all()


class WalleBot(commands.Bot):
    def __init__(self):
        self.bot_channel_manager = BotChannelManager(wall_e_config, self)
        super().__init__(command_prefix='.', intents=intents, help_command=EmbedHelpCommand())
        self.uploading = False

    async def setup_hook(self) -> None:
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
            bot.tree.interaction_check = check_slash_command_test_environment

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


async def check_slash_command_test_environment(interaction: Interaction) -> bool:
    """
    Ensures that the slash command is only processed if its in the correct channel in the TEST
     guild
    :param config: the WallEConfig object necessary to determine the correct channel names
     for processing slash command in the TEST guild
    :param interaction: the interaction object that is in the command's parameter
     for a slash command
    :return:
    """
    text_bot_channel_name = f"{wall_e_config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
    correct_test_guild_text_channel = (
        interaction.guild is not None and
        (
            interaction.channel.name == text_bot_channel_name or
            interaction.channel.name == wall_e_config.get_config_value('basic_config', 'BRANCH_NAME').lower())
    )
    if interaction.guild is None:
        return True
    if not correct_test_guild_text_channel:
        raise Exception("command called from wrong channel")


@bot.event
async def on_ready():
    """
    indicator that all functions that use "wait_until_ready" will start running soon
    :return:
    """
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
    logger.info(f"[main.py on_ready()] {bot.user.name} is now ready for commands")


@bot.listen(name="on_ready")
async def delete_help_command_messages():
    while True:
        try:
            help_messages = await HelpMessage.get_messages_to_delete()
            for help_message in help_messages:
                channel = bot.get_channel(int(help_message.channel_id))
                if channel is not None:
                    successful = False
                    try:
                        message = await channel.fetch_message(int(help_message.message_id))
                        await message.delete()
                        successful = True
                    except discord.NotFound:
                        logger.error(
                            "[main.py delete_help_command_messages()] "
                            f"could not find the message that contains the help command with obj "
                            f"{help_message}"
                        )
                        # setting successful True since the message seems to already be deleted
                        successful = True
                    except discord.Forbidden:
                        logger.error(
                            "[main.py delete_help_command_messages()] "
                            f"wall_e does not seem to have permissions to view/delete the message that "
                            f"contains the help command with obj {help_message}"
                        )
                        # if wall_e does not have the permission to delete the message,
                        # a retry would not fix that anyways
                        successful = True
                    except discord.HTTPException:
                        logger.error(
                            "[main.py delete_help_command_messages()] "
                            f"some sort of HTTP prevented wall_e from deleting the message that "
                            f"contains the help command with obj {help_message}"
                        )
                        # there might be a momentary network glitch, best to try again
                    if successful:
                        await HelpMessage.delete_message(help_message)
        except Exception as error:
            print_wall_e_exception(error, error.__traceback__, error_logger=logger.error)
        await asyncio.sleep(60)


@bot.event
async def on_message(message):
    """
    Function that gets called any input or output from the script
    :param message:
    :return:
    """
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


@bot.event
async def on_app_command_completion(interaction: discord.Interaction, cmd: discord.app_commands.commands.Command):
    """
    Function that gets called whenever a slash command gets called, being use for data gathering purposes
    :param interaction:
    :param cmd:
    :return:
    """
    database_enabled = wall_e_config.enabled("database_config", option="ENABLED")
    if database_enabled:
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
        author=bot.user.display_name,
        avatar_url=bot.user.display_avatar.url,
        description=message,
    )
    if e_obj is not False:
        message = await channel.send(embed=e_obj)
        await asyncio.sleep(10)
        await message.delete()


@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error):
    """
    Function that gets called when the script cant understand the slash command that the user invoked
    :param interaction:
    :param error:
    :return:
    """
    correct_channel = await bot.tree.interaction_check(interaction)
    if correct_channel:
        if isinstance(error, commands.MissingRequiredArgument):
            logger.error(f'[main.py on_command_error()] Missing argument: {error.param}')
            e_obj = await imported_embed(
                logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar_url=interaction.client.user.display_avatar.url,
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
        super(DiscordPyDebugStreamHandler, self).__init__()

    def emit(self, record):
        if record.name != 'discord.py':
            for handler in discordpy_logger.handlers:
                if record.levelno >= handler.level:
                    handler.emit(record)


####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    logger.info("[main.py] Wall-E is starting up")

    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(wall_e_config.get_config_value("basic_config", "TOKEN"), log_handler=DiscordPyDebugStreamHandler())
