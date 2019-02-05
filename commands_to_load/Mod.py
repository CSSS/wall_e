from discord.ext import commands
import discord
import asyncio
import json
from helper_files.embed import embed as em
import helper_files.settings as settings

import logging
logger = logging.getLogger('wall_e')

class Mod():

    async def rekt(self, ctx):
        logger.info('[Mod rekt()] sending troll to unauthorized user')
        lol = '[secret](https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
        eObj = em(title='Minion Things', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=lol)        
        msg = await ctx.send(embed=eObj)
        await asyncio.sleep(5)
        await msg.delete()
        logger.info('[Mod rekt()] troll message deleted')
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['em'])
    async def embed(self, ctx, *arg):
        logger.info('[Mod embed()] embed function detected by user ' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod embed()] invoking message deleted')

        if not arg:
            logger.info("[Mod embed()] no args, so command ended")
            return
        
        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod embed()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return
        
        logger.info('[Mod embed()] minion confirmed')
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

    @commands.command(aliases=['warn'])
    async def modspeak(self, ctx, *arg):
        logger.info('[Mod modspeak()] modspeack function detected by minion ' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod embed()] invoking message deleted')

        if not arg:
            logger.info("[Mod modspeak()] no args, so command ended")
            return

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod modspeak()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        msg = ''
        for wrd in arg:
            msg += wrd + ' '

        eObj = em(title='A Bellow From the Underworld says...', colour=0xff0000, author=ctx.author.display_name, avatar=ctx.author.avatar_url, description=msg, footer='Moderator Warning')
        await ctx.send(embed=eObj)

    @commands.command(aliases=['propm'])
    async def propigatemute(self, ctx):
        """Ensures all channels have the muted role as part of its permissions.""" 
        ## Avoid the admin category of channels and rules and announcments channel since nobody can talk in there anyway

        logger.info('[Mod propigatemute()] propigatemute function detected by user ' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod propigatemute()] invoking message deleted')
        
        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod propigatemute()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        roles = ctx.guild.roles
        for role in roles: 
            if role.id == 338575090847580160: # convert to envVar
                MUTED_ROLE = role
                break

        ignoreChannels = [
                        417758181784158239, # rules
                        228767328106446860, # announcements
                        228766474972430336, # execs
                        303276909054132242, # council
                        478776321808269322, # bot_logs
                        440742806475112448, # deepexec
                        229508956664496130, # meetingroom
                        466734608726229005, # bot-mangement
                        415337971387203585, # sv18
                        444040481677246464, # execs-academicplan
                        420698199712595968 # froshweek-volunteers
                        ]
        # mute role id: <@&338575090847580160>
        # have list of admin channel id's dont get them dynamically in code
        #  waste of cycles, only case for needing it in code if channels get added
        #  however admin channels are rare to be made

        # get guild
        channels = ctx.guild.channels
        # set up the perms overwrite
        overwrite = discord.PermissionOverwrite()
        setattr(overwrite, 'send_messages', False)
        setattr(overwrite, 'manage_messages', False)
        setattr(overwrite, 'manage_channels', False)
        setattr(overwrite, 'manage_guild', False)
        setattr(overwrite, 'manage_nicknames', False)
        setattr(overwrite, 'manage_roles', False)
        
        # loop through channels and change the perms
        for channel in channels: 
            if channel.id not in ignoreChannels:
                print(str(channel.id) + ' ' + channel.name)
                await channel.set_permissions(MUTED_ROLE, overwrite=overwrite)

    @commands.command()
    async def slowmode(self, ctx, time = 10): 
        logger.info('[Mod slowmode()] slowmode function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod slowmode()] invoking message deleted')

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod slowmode()] unathoriezed command attempt detected. Being handled.')
            await self.rekt(ctx)
            return
         
        await ctx.message.channel.edit(slowmode_delay=time, reason=None)
        logger.info('[Mod slowmode()] slowmode enable on channel: ' + str(ctx.message.channel) + ', time between messages set to ' + str(time))

    @commands.command()
    async def makechannel(self, ctx, name, secret = 0):
        logger.info('[Mod makechannel()] makechannel function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod makechannel()] invoking command deleted')

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod makechannel()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        # Verify args
        if not name: 
            eObj = em(description='Missing arguments', footer='Error in makechannel command')
            ctx.send(embed=eObj)
            return

        # Get the MUTED role
        roles = ctx.guild.roles
        for role in roles: 
            if role.id == 338575090847580160:
                MUTED_ROLE = role
                break

        overwrite = {
            ctx.guild.default_role : discord.PermissionOverwrite(mention_everyone=False),
            MUTED_ROLE : discord.PermissionOverwrite()
        }
        
        # Set the Muted roles permissions
        setattr(overwrite[MUTED_ROLE], 'send_messages', False)
        setattr(overwrite[MUTED_ROLE], 'manage_messages', False)
        setattr(overwrite[MUTED_ROLE], 'manage_channels', False)
        setattr(overwrite[MUTED_ROLE], 'manage_guild', False)
        setattr(overwrite[MUTED_ROLE], 'manage_nicknames', False)
        setattr(overwrite[MUTED_ROLE], 'manage_roles', False)

        logger.info('[Mod makechannel()] channel permissions created')

        # Check if making secret channel then append those perms
        if secret: 
            setattr(overwrite[ctx.guild.default_role], 'read_messages', False)
            setattr(overwrite[ctx.guild.default_role], 'manage_messages', False)
            setattr(overwrite[ctx.guild.default_role], 'mention_everyone', True)
            logger.info('[Mod makechannel()] making a hidden channel')

        # Create channel
        ch = await ctx.guild.create_text_channel(name, overwrites=overwrite)
        logger.info('[Mod makechannel()] channel "' + name + '" made by ' + str(ctx.author))

        # Send message to council about channel made 
        council = discord.utils.get(ctx.guild.channels, name="council")
        eObj = em(description=str(ctx.author) + ' made channel: `' + name + '`', footer='Moderator action')
        await council.send(embed=eObj)

    @commands.command()
    async def lock(self, ctx):
        logger.info('[Mod lock()] lock function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod lock()] invoking message deleted')

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod lock()] unauthorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return
        # Lock will set @everyone send messages permission to false
        # Might have ot set @Minions to be able to talk (also Omnipotent)
        # then send a message to council 
        MINIONS_ROLE = discord.utils.get(ctx.guild.roles, name='Minions')

        channel = ctx.message.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await channel.set_permissions(MINIONS_ROLE, send_messages=True)
        logger.info('[Mod lock()] channel "' + str(ctx.message.channel.name) + '" locked')

        eObj = em(description='Channel locked until the mods stop abusing their power', colour=0xff0000, footer='Moderator Action')
        await ctx.send(embed=eObj)
        logger.info('[Mod lock()] message sent to indicate locked channel')

#TODO: lock commands, dm warn/other kind of dm'd info etc, mass msg delete, mute


def setup(bot):
    bot.add_cog(Mod(bot))
