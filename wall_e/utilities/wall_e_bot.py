import logging
import time
from typing import Optional, Sequence

import discord
from discord import Intents, Message
from discord.abc import Snowflake
from discord.ext import commands
from discord.ext.commands import Cog
from discord.utils import MISSING

from utilities.global_vars import wall_e_config, logger, sys_debug_log_file_absolute_path, \
    sys_error_log_file_absolute_path, wall_e_debug_log_file_absolute_path, wall_e_error_log_file_absolute_path, \
    discordpy_debug_log_file_absolute_path, discordpy_error_log_file_absolute_path, \
    incident_report_debug_log_file_absolute_path, sys_warn_log_file_absolute_path, \
    wall_e_warn_log_file_absolute_path, discordpy_warn_log_file_absolute_path

from extensions.help_commands import EmbedHelpCommand
from overriden_coroutines.delete_help_messages import delete_help_command_messages
from overriden_coroutines.detect_reactions import reaction_detected
from overriden_coroutines.error_handlers import report_text_command_error, report_slash_command_error
from utilities.bot_channel_manager import BotChannelManager
from utilities.discordpy_stream_handler import DiscordPyDebugStreamHandler
from utilities.embed import embed as imported_embed
from utilities.file_uploading import start_file_uploading

intents = Intents.all()

extension_location_python_path = "extensions."


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
        self.tree.on_error = report_slash_command_error
        self.add_listener(reaction_detected, "on_raw_reaction_add")
        delete_help_command_messages.start()

        await self.add_custom_extension()
        logger.debug("[wall_e_bot.py] extensions loaded")
        await super().setup_hook()

    async def add_custom_extension(self, module_path_and_name: str = None):
        adding_all_extensions = module_path_and_name is None
        extension_unloaded = False
        for extension in wall_e_config.get_extensions():
            if extension_unloaded:
                break
            try:
                logger.debug(f"[wall_e_bot.py] attempting to load extension {extension} ")
                # the below piece of logic will not work well in the test guild if there
                # are multiple PRs being worked on at the same time that have different
                # slash command as there is no way to avoid a conflict. I tried to fix this
                # by having the bot in multiple guilds, one for each PR, but if an extension is loaded to wall_e
                # after the on_ready signal has already been received, any on_ready functions in the extension
                # that is loaded will not be run, which is a pre-req for almost all the extensions
                await self.load_extension(extension)
                logger.debug(f"[wall_e_bot.py] {extension} successfully loaded")
                if not adding_all_extensions:
                    extension_unloaded = True
                    break
            except Exception as err:
                exception = f'{type(err).__name__}: {err}'
                logger.error(f'[wall_e_bot.py] Failed to load extension {extension}\n{exception}')
                if adding_all_extensions:
                    time.sleep(20)
                    exit(1)

    async def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
        extension_name = name if extension_location_python_path in name else f"{extension_location_python_path}{name}"
        await super(WalleBot, self).load_extension(extension_name, package=package)

    async def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        extension_name = name if extension_location_python_path in name else f"{extension_location_python_path}{name}"
        await super(WalleBot, self).unload_extension(extension_name, package=package)

    async def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        await super(WalleBot, self).reload_extension(f"{extension_location_python_path}{name}", package=package)

    async def add_cog(
        self,
        cog: Cog,
        /,
        *,
        override: bool = False,
        guild: Optional[Snowflake] = MISSING,
        guilds: Sequence[Snowflake] = MISSING,
    ) -> None:
        guild = discord.Object(id=int(wall_e_config.get_config_value("basic_config", "GUILD_ID")))
        await super(WalleBot, self).add_cog(cog, override=override, guild=guild, guilds=guilds)

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
        if self.uploading is False:
            try:
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, sys_debug_log_file_absolute_path, "sys_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, sys_warn_log_file_absolute_path, "sys_warn"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, sys_error_log_file_absolute_path, "sys_error"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, wall_e_debug_log_file_absolute_path, "wall_e_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, wall_e_warn_log_file_absolute_path, "wall_e_warn"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, wall_e_error_log_file_absolute_path, "wall_e_error"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, discordpy_debug_log_file_absolute_path, "discordpy_debug"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, discordpy_warn_log_file_absolute_path, "discordpy_warn"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, discordpy_error_log_file_absolute_path, "discordpy_error"
                )
                await start_file_uploading(
                    logger, bot_guild, self, wall_e_config, incident_report_debug_log_file_absolute_path,
                    wall_e_config.get_config_value('channel_names', 'INCIDENT_REPORT_CHANNEL'),
                    categorized_channel=False
                )
                await self.bot_channel_manager.create_or_get_channel_id(
                    logger, bot_guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
                    wall_e_config.get_config_value('channel_names', 'EMBED_AVATAR_CHANNEL'),
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_debug"
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_warn"
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_error"
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_discordpy_debug"
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_discordpy_warn"
                )
                await self.bot_channel_manager.create_or_get_channel_id_for_service(
                    logger, bot_guild, wall_e_config, "member_update_listener_discordpy_error"
                )
                await self.bot_channel_manager.fix_text_channel_positioning(logger, guild=bot_guild)
                self.uploading = True
            except Exception as e:
                raise Exception(
                    "[wall_e_bot.py] Could not open log file to read from and sent entries to bot_log channel due to "
                    f"following error {e}")
        logger.info('[wall_e_bot.py on_ready()] Logged in as')
        logger.info(f'[wall_e_bot.py on_ready()] {self.user.name}({self.user.id})')
        logger.info('[wall_e_bot.py on_ready()] ------')
