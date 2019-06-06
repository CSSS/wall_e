import os # noqa, flake8 F401
import discord
from discord.ext import commands
from main import settings
import logging
logger = logging.getLogger('wall_e')


class TestCog:

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        logger.info("[testenv.py debuginfo()] debuginfo command detected from " + str(ctx.message.author))
        if settings.ENVIRONMENT == 'TEST':
            fmt = '```You are testing the latest commit of branch or pull request: {0}```'
            await ctx.send(fmt.format(settings.BRANCH_NAME))
        return

    # this command is used by the TEST guild to ensur that each TEST container will only process incoming commands
    # that originate from channels that match the name of their branch
    @staticmethod
    def check_test_environment(ctx):
        if settings.ENVIRONMENT == 'TEST':
            if ctx.message.guild is not None and ctx.channel.name != settings.BRANCH_NAME.lower():
                return False
        return True

    # this command is used by the TEST guild to create the channel from which this TEST container will process
    # commands
    async def on_ready(self):
        if settings.ENVIRONMENT == 'TEST':
            logger.info("[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels))
            if discord.utils.get(self.bot.guilds[0].channels, name=settings.BRANCH_NAME.lower()) is None:
                logger.info("[testenv.py on_ready()] creating the text channel " + settings.BRANCH_NAME.lower())
                await self.bot.guilds[0].create_text_channel(settings.BRANCH_NAME.lower())

    def __init__(self, bot):
        logger.info("[testenv.py __init__()] initializing the TestCog")
        bot.add_check(self.check_test_environment)
        self.bot = bot


def setup(bot):
    bot.add_cog(TestCog(bot))
