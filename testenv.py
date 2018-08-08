import os
import discord
from discord.ext import commands

ENVIRONMENT = os.environ['ENVIRONMENT']


class TestCog:

    @commands.command()
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

    def __init__(self, bot):
        bot.add_check(self.check_test_environment)
        bot.add_command(self.debuginfo)
        bot.add_listener(self.on_ready)
        self.bot = bot


def setup(bot):
    bot.add_cog(TestCog(bot))
