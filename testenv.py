import os
import discord

ENVIRONMENT = os.environ['ENVIRONMENT']


async def check_test_environment(ctx):
    if ENVIRONMENT == 'TEST':
        branch = os.environ['BRANCH'].lower()
        if discord.utils.get(ctx.guild.channels, name=branch) is None:
            await ctx.guild.create_text_channel(branch)
        if ctx.channel.name != branch:
            return False
    return True


class TestCog:

    def __init__(self, bot):
        bot.add_check(check_test_environment)
        self.bot = bot


def setup(bot):
    bot.add_cog(TestCog(bot))
