import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class HealthChecks(commands.Cog):

    def __init__(self, bot, config, bot_channel_manager):
        log_info = Loggers.get_logger(logger_name="HealthChecks")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.config = config
        self.guild = None
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
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path,
                "health_checks_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path,
                "health_checks_error"
            )

    @app_commands.command(name="ping", description="return pong!")
    async def ping(self, interaction: discord.Interaction):
        self.logger.info(f"[HealthChecks ping()] ping command detected from {interaction.user}")
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            description='Pong!',
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR')
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)

    @app_commands.command(name="echo", description="repeats what the user said back at them")
    @app_commands.describe(string="string to echo")
    async def echo(self, interaction: discord.Interaction, string: str):
        user = interaction.user.display_name
        self.logger.info(
            f"[HealthChecks echo()] echo command detected from {interaction.user} with argument {string}"
        )
        avatar = interaction.user.avatar.url
        e_obj = await embed(
            self.logger, interaction=interaction, author=user, avatar=avatar, description=string
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)
