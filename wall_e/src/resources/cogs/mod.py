from discord.ext import commands
import discord
import asyncio
# import json
from resources.utilities.embed import embed as em

import logging
logger = logging.getLogger('wall_e')


class Mod(commands.Cog):

    async def rekt(self, ctx):
        logger.info('[Mod rekt()] sending troll to unauthorized user')
        lol = '[secret](https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
        e_obj = await em(
            ctx_obj=ctx.send,
            title='Minion Things',
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=lol
        )
        if e_obj is not False:
            msg = await ctx.send(embed=e_obj)
            await asyncio.sleep(5)
            await msg.delete()
            logger.info('[Mod rekt()] troll message deleted')

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    @commands.command(aliases=['em'])
    async def embed(self, ctx, *arg):
        logger.info('[Mod embed()] embed function detected by user {}'.format(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod embed()] invoking message deleted')

        if not arg:
            logger.info("[Mod embed()] no args, so command ended")
            return

        if ctx.message.author not in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod embed()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        logger.info('[Mod embed()] minion confirmed')
        fields = []
        desc = ''
        arg = list(arg)
        arg_len = len(arg)
        # odd number of args means description plus fields
        if not arg_len % 2 == 0:
            desc = arg[0]
            arg.pop(0)
            arg_len = len(arg)

        i = 0
        while i < arg_len:
            fields.append([arg[i], arg[i + 1]])
            i += 2

        name = ctx.author.nick or ctx.author.name
        e_obj = await em(
            ctx_obj=ctx.send, description=desc, author=name, avatar=ctx.author.avatar.url, colour=0xffc61d,
            content=fields
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)

    @commands.command(aliases=['warn'])
    async def modspeak(self, ctx, *arg):
        logger.info('[Mod modspeak()] modspeack function detected by minion {}'.format(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod modspeak()] invoking message deleted')

        if not arg:
            logger.info("[Mod modspeak()] no args, so command ended")
            return

        if ctx.message.author not in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod modspeak()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        msg = ''
        for wrd in arg:
            msg += '{} '.format(wrd)

        e_obj = await em(ctx_obj=ctx.send, title='ATTENTION:', colour=0xff0000, author=ctx.author.display_name,
                         avatar=ctx.author.avatar.url, description=msg, footer='Moderator Warning')
        if e_obj is not False:
            await ctx.send(embed=e_obj)
