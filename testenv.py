import os
import discord
import main
from discord.ext import commands

ENVIRONMENT = os.environ['ENVIRONMENT']


class TestCog:

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        if ENVIRONMENT == 'TEST':
            branch = os.environ['BRANCH']
            fmt = '```You are testing the latest commit of branch or pull request: {0}```'
            await ctx.send(fmt.format(branch))
        return

    @staticmethod
    def check_test_environment(ctx):
        if ENVIRONMENT == 'TEST':
            branch = os.environ['BRANCH'].lower()
            if ctx.channel.name != branch:
                return False
        return True

    async def on_ready(self):
        if ENVIRONMENT == 'TEST':
            branch = os.environ['BRANCH'].lower()
            if discord.utils.get(self.bot.guilds[0].channels, name=branch) is None:
                await self.bot.guilds[0].create_text_channel(branch)
            log_channel = discord.utils.get(self.bot.guilds[0].channels, name=branch + '_logs')
            if log_channel is None:
                log_channel = await self.bot.guilds[0].create_text_channel(branch + '_logs')
            main.BOT_LOG_CHANNEL = log_channel.id

    def __init__(self, bot):
        bot.add_check(self.check_test_environment)
        self.bot = bot


def setup(bot):
    bot.add_cog(TestCog(bot))
