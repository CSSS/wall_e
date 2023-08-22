import discord
from discord import app_commands
from discord.ext import commands
from resources.utilities.embed import embed
import logging

from resources.utilities.slash_command_checks import slash_command_checks

logger = logging.getLogger('wall_e')


class HealthChecks(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.help_dict = self.config.get_help_json()

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        await slash_command_checks(self.config, interaction, self.help_dict)
        logger.info("[HealthChecks ping()] ping command detected from {}".format(interaction.user))
        e_obj = await embed(
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
        await slash_command_checks(self.config, interaction, self.help_dict)
        user = interaction.user.display_name
        logger.info("[HealthChecks echo()] echo command "
                    "detected from {} with argument {}".format(interaction.user, user_input))
        avatar = interaction.user.avatar.url
        e_obj = await embed(
            interaction=interaction, author=user, avatar=avatar, description=user_input
        )
        if e_obj is not False:
            await interaction.response.send_message(embed=e_obj)
