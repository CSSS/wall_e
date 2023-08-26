import discord
from discord import app_commands
from discord.ext import commands

from resources.utilities.embed import embed
from resources.utilities.file_uploading import start_file_uploading
from resources.utilities.get_guild import get_guild
from resources.utilities.setup_logger import Loggers
from resources.utilities.slash_command_checks import slash_command_checks


class HealthChecks(commands.Cog):

    def __init__(self, bot, config, bot_loop_manager):
        log_info = Loggers.get_logger(logger_name="HealthChecks")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.config = config
        self.guild = get_guild(self.bot, self.config)
        self.bot_loop_manager = bot_loop_manager
        self.help_dict = self.config.get_help_json()

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        await start_file_uploading(
            self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path, "health_checks_debug"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        await start_file_uploading(
            self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path, "health_checks_error"
        )

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        await slash_command_checks(self.logger, self.config, interaction, self.help_dict)
        self.logger.info("[HealthChecks ping()] ping command detected from {}".format(interaction.user))
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
        await slash_command_checks(self.logger, self.config, interaction, self.help_dict)
        user = interaction.user.display_name
        self.logger.info("[HealthChecks echo()] echo command "
                         "detected from {} with argument {}".format(interaction.user, string)
                         )
        avatar = interaction.user.avatar.url
        e_obj = await embed(
            self.logger, interaction=interaction, author=user, avatar=avatar, description=string
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)
