from discord.ext import commands
import discord
import asyncio
import json
from helper_files.embed import embed as em
import helper_files.settings as settings

import logging
logger = logging.getLogger('wall_e')

class Mod():

    def isMinion(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name='Minions')
        membersOfRole = role.members
        for members in membersOfRole:
            if ctx.author.id == members.id:
                return True
        return False

    async def rekt(self, ctx):
        lol = '[secret](https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
        eObj = em(title='Minion Things', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=lol)        
        await ctx.send(embed=eObj)
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def embed(self, ctx, *arg):
        logger.info('[Mod embed()] embed function detected by minion ' + str(ctx.message.author))
        if not self.isMinion(ctx):
            await self.rekt(ctx)
            return
        
        logger.info('[Mod embed()] parsing args')
        fields = []
        desc = ''
        arg = list(arg)
        argLen = len(arg)
        # odd number of args means description plus fields
        if not argLen%2 == 0:
            desc = arg[0]
            arg.pop(0)
            argLen = len(arg)
            
        i = 0
        while i < argLen:
            fields.append([arg[i], arg[i+1]])
            i +=2

        name = ctx.author.nick or ctx.author.name
        eObj = em(description=desc, author=name, avatar=ctx.author.avatar_url, colour=0xffc61d ,content=fields)
        await ctx.send(embed=eObj)

def setup(bot):
    bot.add_cog(Mod(bot))
