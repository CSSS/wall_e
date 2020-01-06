from discord.ext import commands
from resources.utilities.embed import embed
import logging
logger = logging.getLogger('wall_e')


def get_class_name():
    return "HealthChecks"


class HealthChecks(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    @commands.command()
    async def ping(self, ctx):
        logger.info("[HealthChecks ping()] ping command detected from {}".format(ctx.message.author))
        e_obj = await embed(
            ctx,
            description='Pong!',
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR')
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)

    @commands.command()
    async def echo(self, ctx, *args):
        user = ctx.author.display_name
        arg = ''
        for argument in args:
            arg += '{} '.format(argument)
        logger.info("[HealthChecks echo()] echo command "
                    "detected from {} with argument {}".format(ctx.message.author, arg))
        avatar = ctx.author.avatar_url
        e_obj = await embed(ctx, author=user, avatar=avatar, description=arg)
        if e_obj is not False:
            await ctx.send(embed=e_obj)
