from discord.ext import commands
from helper_files.embed import embed
import helper_files.settings as settings

import logging
logger = logging.getLogger('wall_e')


class HealthChecks():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        logger.info("[HealthChecks ping()] ping command detected from " + str(ctx.message.author))
        eObj = await embed(ctx, description='Pong!', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR)
        if eObj is not False:
            await ctx.send(embed=eObj)

    @commands.command()
    async def echo(self, ctx, *args):
        user = ctx.author.display_name
        arg = ''
        for argument in args:
            arg += argument + ' '
        logger.info("[HealthChecks echo()] echo command detected from " + str(ctx.message.author) + " with argument "
                    + str(arg))
        avatar = ctx.author.avatar_url
        eObj = await embed(ctx, author=user, avatar=avatar, description=arg)
        if eObj is not False:
            await ctx.send(embed=eObj)


def setup(bot):
    bot.add_cog(HealthChecks(bot))
