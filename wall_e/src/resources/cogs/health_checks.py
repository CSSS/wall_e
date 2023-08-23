import discord
from discord import app_commands
from discord.ext import commands
from resources.utilities.embed import embed
from resources.utilities.log_channel import write_to_bot_log_channel
from resources.utilities.setup_logger import Loggers

from resources.utilities.slash_command_checks import slash_command_checks


class HealthChecks(commands.Cog):

    def __init__(self, bot, config, bot_loop_manager):
        self.bot = bot
        self.config = config
        self.bot_loop_manager = bot_loop_manager
        self.logger, self.debug_log_file_absolute_path, self.sys_stream_error_log_file_absolute_path \
            = Loggers.get_logger(logger_name="HealthChecks")
        self.help_dict = self.config.get_help_json()

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        chan_id = await self.bot_loop_manager.create_or_get_channel_id_for_service(
            self.config,
            "health_checks_debug"
        )
        await write_to_bot_log_channel(
            self.bot, self.debug_log_file_absolute_path, chan_id
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        chan_id = await self.bot_loop_manager.create_or_get_channel_id_for_service(
            self.config,
            "health_checks_error"
        )
        await write_to_bot_log_channel(
            self.bot, self.sys_stream_error_log_file_absolute_path, chan_id
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

    @app_commands.command(name="echo", description="echo command")
    @app_commands.describe(user_input="string to echo")
    async def echo(self, interaction: discord.Interaction, user_input: str):
        await slash_command_checks(self.logger, self.config, interaction, self.help_dict)
        user = interaction.user.display_name
        self.logger.info("[HealthChecks echo()] echo command "
                         "detected from {} with argument {}".format(interaction.user, user_input)
                         )
        avatar = interaction.user.avatar.url
        e_obj = await embed(
            self.logger, interaction=interaction, author=user, avatar=avatar, description=user_input
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)
