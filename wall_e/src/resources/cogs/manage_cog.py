import discord
from discord.ext import commands
import logging
logger = logging.getLogger('wall_e')


def getClassName():
    return "ManageCog"


class ManageCog(commands.Cog):

    def __init__(self, bot, config):
        logger.info("[testenv.py __init__()] initializing the TestCog")
        bot.add_check(self.check_test_environment)
        self.bot = bot
        self.config = config

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        logger.info("[testenv.py debuginfo()] debuginfo command detected from " + str(ctx.message.author))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            fmt = '```You are testing the latest commit of branch or pull request: {0}```'
            await ctx.send(fmt.format(self.config.get_config_value('database', 'BRANCH_NAME')))
        return

    # this command is used by the TEST guild to ensur that each TEST container will only process incoming commands
    # that originate from channels that match the name of their branch
    def check_test_environment(self, ctx):
        if self.config.get_config_value('basic_config', 'BRANCH_NAME') == 'TEST':
            if ctx.message.guild is not None and\
               ctx.channel.name != self.config.get_config_value('basic_config', 'BRANCH_NAME').lower():
                return False
        return True

    # this command is used by the TEST guild to create the channel from which this TEST container will process
    # commands
    async def on_ready(self):
        logger.info("[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            logger.info(
                "[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels)
            )
            channels = self.bot.guilds[0].channels
            branch_name = self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
            if discord.utils.get(channels, name=branch_name) is None:
                logger.info(
                    "[testenv.py on_ready()] creating the text channel"
                    " " + self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
                    )
                await self.bot.guilds[0].create_text_channel(branch_name)
