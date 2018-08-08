import os
import discord
from discord.ext import commands

ENVIRONMENT = os.environ['ENVIRONMENT']


def filter_remindme_test_environment(ctx):
    if ENVIRONMENT == 'TEST':
        branch = os.environ['BRANCH'].lower()
        if ctx.channel.name != branch:
            return False
    return True


async def check_test_environment(ctx):
    if ENVIRONMENT == 'TEST':
        branch = os.environ['BRANCH'].lower()
        if discord.utils.get(ctx.guild.channels, name=branch) is None:
            await ctx.guild.create_text_channel(branch)
        if ctx.channel.name != branch:
            return False
    return True


@commands.command()
async def debuginfo(ctx):
    if ENVIRONMENT == 'TEST':
        branch = os.environ['BRANCH']
        fmt = '```You are testing the latest commit of branch or pull request: {0}```'
        await ctx.send(fmt.format(branch))
    return


class TestCog:

    def __init__(self, bot):
        bot.add_check(check_test_environment)
        bot.add_command(debuginfo)
        self.bot = bot


def setup(bot):
    bot.add_cog(TestCog(bot))
