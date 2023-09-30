import importlib
import inspect
import logging
import sys
import time
from typing import Optional

import discord
from discord import Intents, Message
from discord.ext import commands
from discord.utils import MISSING

from cogs.help_commands import EmbedHelpCommand
from overriden_coroutines.delete_help_messages import delete_help_command_messages
from overriden_coroutines.detect_reactions import reaction_detected
from overriden_coroutines.error_handlers import report_text_command_error, report_slash_command_error
from utilities.bot_channel_manager import BotChannelManager
from utilities.discordpy_stream_handler import DiscordPyDebugStreamHandler
from utilities.embed import embed as imported_embed
from utilities.file_uploading import start_file_uploading
from utilities.global_vars import wall_e_config, logger, sys_debug_log_file_absolute_path, \
    sys_error_log_file_absolute_path, wall_e_debug_log_file_absolute_path, wall_e_error_log_file_absolute_path, \
    discordpy_debug_log_file_absolute_path, discordpy_error_log_file_absolute_path

intents = Intents.all()


class WalleBot(commands.Bot):
    def __init__(self):
        self.bot_channel_manager = BotChannelManager(wall_e_config, self)
        self.listeners = []
        super().__init__(command_prefix='.', intents=intents, help_command=EmbedHelpCommand())
        self.uploading = False

    def run(
        self, token: str = None, *, reconnect: bool = True, log_handler: Optional[logging.Handler] = MISSING,
            log_formatter: logging.Formatter = MISSING, log_level: int = MISSING, root_logger: bool = False) -> None:
        logger.info("[wall_e_bot.py] Wall-E is starting up")
        super(WalleBot, self).run(
            token,
            log_handler=DiscordPyDebugStreamHandler()
        )

    async def setup_hook(self) -> None:
        self.add_listener(report_text_command_error, "on_command_error")
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            self.tree.on_error = report_slash_command_error
        self.add_listener(reaction_detected, "on_raw_reaction_add")
        self.add_listener(delete_help_command_messages, "on_ready")

        await self.add_custom_cog()
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
                        cog_class_matches_file_name = (
                            cog_class_to_load.__name__.lower() == cog['name'].lower().replace("_", "")
                        )
                        if type(cog_class_to_load) is commands.cog.CogMeta and cog_class_matches_file_name:
                            logger.info(
                                f"[main.py] attempting to load cog {cog_class_to_load.__name__} "
                                f"under file {cog['name']}"
                            )
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
                            logger.info(f"[main.py] {cog_class_to_load.__name__} successfully loaded")
                            if not adding_all_cogs:
                                cog_unloaded = True
                                break
            except Exception as err:
                exception = f'{type(err).__name__}: {err}'
                logger.error(f'[main.py] Failed to load command {cog}\n{exception}')
                if adding_all_cogs:
                    time.sleep(20)
                    exit(1)

    async def on_message(self, message: Message, /) -> None:
        """
        Function that gets called any input or output from the script
        :param message:
        :return:
        """
        if message.guild is None and message.author != self.user:
            em = await imported_embed(
                logger,
                ctx=message.author,
                description="[welcome to the machine](https://platform.openai.com/login?launch)"
            )
            if em is not None:
                await message.author.send(embed=em)
        else:
            await self.process_commands(message)

    async def on_ready(self):
        """
        indicator that all functions that use "wait_until_ready" will start running soon
        :return:
        """
        bot_guild = self.guilds[0]
        # tries to open log file in prep for write_to_bot_log_channel function
        if self.uploading is False and wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            try:
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, sys_debug_log_file_absolute_path, "sys_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, sys_error_log_file_absolute_path, "sys_error"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, wall_e_debug_log_file_absolute_path, "wall_e_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, wall_e_error_log_file_absolute_path, "wall_e_error"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, discordpy_debug_log_file_absolute_path, "discordpy_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, discordpy_error_log_file_absolute_path, "discordpy_error"
                )
                await self.bot_channel_manager.create_or_get_channel_id(
                    logger, bot_guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
                    wall_e_config.get_config_value('channel_names', 'EMBED_AVATAR_CHANNEL')
                )
                self.uploading = True
            except Exception as e:
                raise Exception(
                    "[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                    f"following error {e}")
        logger.info('[main.py on_ready()] Logged in as')
        logger.info(f'[main.py on_ready()] {self.user.name}({self.user.id})')
        logger.info('[main.py on_ready()] ------')
