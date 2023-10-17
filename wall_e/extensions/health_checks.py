import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class HealthChecks(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="HealthChecks")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[HealthChecks __init__()] initializing HealthChecks")
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
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path,
                "health_checks_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path, "health_checks_warn"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path,
                "health_checks_error"
            )

    @app_commands.command(name="ping", description="return pong!")
    @app_commands.checks.has_role("Bot_manager")
    async def ping(self, interaction: discord.Interaction):
        self.logger.info(f"[HealthChecks ping()] ping command detected from {interaction.user}")
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            description='Pong!',
            author=interaction.client.user,
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)

    @app_commands.command(name="echo", description="repeats what the user said back at them")
    @app_commands.describe(string="string to echo")
    async def echo(self, interaction: discord.Interaction, string: str):
        self.logger.info(
            f"[HealthChecks echo()] echo command detected from {interaction.user} with argument {string}"
        )
        e_obj = await embed(
            self.logger, interaction=interaction, author=interaction.user,
            description=string
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)


async def setup(bot):
    await bot.add_cog(HealthChecks())
