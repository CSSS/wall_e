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

        MUTED_ROLE = discord.utils.get(ctx.guild.roles, name='Muted')

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

        # Get guild
        channels = ctx.guild.channels

        # Set up the perms overwrite
        overwrite = discord.PermissionOverwrite()
        setattr(overwrite, 'send_messages', False)
        setattr(overwrite, 'manage_messages', False)
        setattr(overwrite, 'manage_channels', False)
        setattr(overwrite, 'manage_guild', False)
        setattr(overwrite, 'manage_nicknames', False)
        setattr(overwrite, 'manage_roles', False)
        
        # Loop through channels and change the perms
        for channel in channels: 
            if channel.id not in ignoreChannels:
                await channel.set_permissions(MUTED_ROLE, overwrite=overwrite)

        eObj = em(description='Muted permissions spread though all channels like herpies. Enjoy :)', footer='Moderator action')
        await ctx.send(embed=eObj, delete_after=3.0)

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
        MUTED_ROLE = discord.utils.get(ctx.guild.roles, name='Muted')

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
    async def clear(self, ctx, numOfMsgs = 10):
        # Deletes the last X (10 by default) msg's from channel
        # Limits: Max 100 messages at a time AND no messages older than 2 weeks (14 days)

        logger.info('[Mod clear()] clear function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod clear()] invoking command deleted')
        
        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod clear()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        # Verify args
        if numOfMsgs > 100: 
            # Prevents discord.ClientException 
            eObj = em(description='Number of messages to be deleted cannot be more than 100', footer='Invalid arguments')
            await ctx.send(embed=eObj)

        channel = ctx.channel
        # Grab the last X messages from the channel regardless of user
        logger.info('[Mod clear()] grabbing last {} message from {}'.format(numOfMsgs, channel))
        messages = await channel.history(limit=numOfMsgs).flatten()
        logger.info('[Mod clear()] messages to be deleted: {}'.format(messages))
        
        try:
            await channel.delete_messages(messages)
            logger.info('[Mod clear()] messages from {} deleted'.format(channel))
        except discord.HTTPException:
            eObj = em(description='Messagaes cannot be older than 2 weeks', footer='Command Error')
            await ctx.send(embed=eObj, delete_after=10.0)
            return

        eObj = em(description='{} messages deleted'.format(numOfMsgs), footer='Message will self destruct in 5 ...')
        await ctx.send(embed=eObj, delete_after=5.0)

    @commands.command()
    async def purge(self, ctx, *args):
        # Deletes 10 message in channel from user
        # Order of arguments doesn't matter, the code works around it
        args = list(args)

        # Verify Minion
        logger.info('[Mod purge()] purge function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod purge()] invoking command deleted')
        
        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod purge()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        # Verify arguments
        logger.info('[Mod purge()] verifying arguments')
        mentions = ctx.message.mentions
        if len(mentions) != 1: 
            # There is no mentoin or more than 1
            eObj = em(description='Need to @ mention the user to purge messages from', footer='Invalid arguments')
            await ctx.send(embed=eObj)
            return
        elif len(mentions) == 1:
            # Remove the mention from args and init the num var
            user = mentions[0]
            args.remove(user.mention)

        if args:
            num = int(args[0])
        else:
            num = 10
        logger.info('[Mod purge()] all arguments verified')
        logger.info('[Mod purge()] to purge messages from: {}\nNumber of messages to purge: {}'.format(user, num))

        # Check command will determine if message is from user. Will need counter
        def check(m):
            nonlocal num
            if m.author == user and num > 0:
                num -=1
                return True
            else:
                return False
            
        # Call channel.purge() limit at 100 and bulk = True
        deleted = await ctx.channel.purge(limit=100, check=check, bulk=True)
        logger.info('[Mod purge()] purged messages: {}'.format(deleted))
        
        eObj = em(description='Purged {} messages from {}'.format(len(deleted), user), footer='This messages will self destruct in 5...')
        await ctx.send(embed=eObj, delete_after=5.0)

    @commands.command()
    async def mute(self, ctx):
        # Adds mute role to someone
        
        # Verify Minion
        logger.info('[Mod mute()] mute function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod mute()] invoking command deleted')
        
        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod mute()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        # Check for mention
        # If there get user
        logger.info('[Mod mute()] checking for mention')
        mentions = ctx.message.mentions
        if len(mentions) != 1:
            logger.info('[Mod mute()] no mention found. Informing user')
            eObj = em(description='You need to @ mention the user to mute', footer='Invalid arguments')
            await ctx.send(embed=eObj, delete_after=5.0)
            return
        else: 
            user = mentions[0]
        logger.info('[Mod mute()] user found through mention: {}'.format(user))

        # Grab the Muted role
        MUTED_ROLE = discord.utils.get(ctx.guild.roles, name='Muted')
        logger.info('[Mod mute()] mute role found: {}'.format(MUTED_ROLE.id))

        # Add muted role to user
        await user.add_roles(MUTED_ROLE)
        logger.info('[Mod mute()] adding muted role to user')

        # Tell them in dm
        logger.info('[Mod mute()] informing {} that they are muted in dm'.format(user))
        eObj = em(title='Moderator action was taken against you', colour=0xff0000, description='You\'ve been muted in the CSSS server. Message a minion to learn why and how to be unmuted', footer='Moderator action')
        await user.send(embed=eObj)
        #TODO add something ^ to react to msg council for reconsideration slash reach out to u

        # Tell council of action 
        logger.info('[Mod mute()] getting council channel')
        council = discord.utils.get(ctx.guild.channels, name='council')
        logger.info('[Mod mute()] council channel found: {}'.format(council.id))

        logger.info('[Mod mute()] informing council of {}\'s action to mute {}'.format(ctx.message.author, user))
        eObj = em(description='{} muted {}'.format(ctx.message.author, user))
        await council.send(embed=eObj)

    @commands.command()
    async def unmute(self, ctx):
        # Unmutes user by removed the muted role from them

        # Verify mention
        logger.info('[Mod unmute()] checking for mention')
        mentions = ctx.message.mentions
        if len(mentions) != 1:
            logger.info('[Mod unmute()] no mention found. Informing user')
            eObj = em(description='You need to @ mention the user to mute', footer='Invalid arguments')
            await ctx.send(embed=eObj, delete_after=5.0)
            return
        else: 
            user = mentions[0]
        logger.info('[Mod unmute()] user found through mention: {}'.format(user))

        # Get muted role
        MUTED_ROLE = discord.utils.get(ctx.guild.roles, name='Muted')
        logger.info('[Mod unmute()] muted role found: {}'.format(MUTED_ROLE.id))

        # Verify user has the muted role
        logger.info('[Mod unmute()] verifying if {} is muted or not'.format(user))
        if user not in MUTED_ROLE.members:
            logger.info('[Mod unmute()] {} is not muted. Informing {} of this fact'.format(user, ctx.message.author))
            eObj = em(description='{} is not muted so cannot unmute'.format(user), footer='Invalid arguments')
            await ctx.send(embed=eObj)
            return
        logger.info('[Mod unmute()] {} verified to be muted'.format(user))

        # Remove role from the user
        await user.remove_roles(MUTED_ROLE)
        logger.info('[Mod unmute()] removed muted role from {}'.format(user))

        # Tell user of their new freedom and to not abuse it
        logger.info('[Mod unmute()] letting {} know they\'ve been unmuted and to not do something stupid again')
        eObj = em(description='You\'ve been unmuted. Don\'t do whatever you did to get muted in the first place again, or else next time you\'ll get more than a ban', footer='Moderator action')
        await user.send(embed=eObj)

        # Inform council of actions
        logger.info('[Mod unmute()] telling council of the unmuting')
        council = discord.utils.get(ctx.guild.channels, name='council')
        await council.send('{} unmuted {}'.format(ctx.message.author, user))

    @commands.command()
    async def lock(self, ctx):
        # Disable everyone perms on channel for sending
        # Add Minions exception to above
        # Tell Council

        logger.info('[Mod lock()] lock function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod lock()] invoking command deleted')

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod lock()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        # Get channel
        channel = ctx.channel
        logger.info('[Mod lock()] channel to unmute: {}'.format(channel.id))

        # Get Minions role
        MINIONS_ROLE = discord.utils.get(ctx.guild.roles, name='Minions')
        logger.info('[Mod lock()] minion role found: {}'.format(MINIONS_ROLE.id))

        # Edit channel with new permissions
        logger.info('[Mod lock()] editing {} permissions'.format(channel))
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await channel.set_permissions(MINIONS_ROLE, send_messages=True)

        # Message channel to notify the status
        logger.info('[Mod lock()] lock message sent to {}'.format(channel))
        eObj = em(description='This channel has been locked until further notice.', author=ctx.author.display_name, avatar=ctx.author.avatar_url, footer='Moderator action')
        await ctx.send(embed=eObj)

        # Inform council of the locked channel
        logger.info('[Mod lock()] council informed of locked channel')
        council = discord.utils.get(ctx.guild.channels, name='council')
        eObj = em(description='{} locked {}'.format(ctx.message.author, channel.mention), footer='Moderator action')
        await council.send(embed=eObj)

    @commands.command()
    async def unlock(self, ctx):
        # Unlocks a channel if its locked
        # Verify channel is locked 
        ## How? => check @everyone for send_messages
        
        logger.info('[Mod unlock()] unlock function detected by user' + str(ctx.message.author))
        await ctx.message.delete()
        logger.info('[Mod unlock()] invoking command deleted')

        if not ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members:
            logger.info('[Mod unlock()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        channel = ctx.channel
        perms = channel.overwrites
        ow = list(perms[0]) # assumes @everyone is always the fifrst thign in teh perms tuple

        if ow[1].send_messages == True or ow[1].send_messages == None: 
            # Not locked
            await ctx.send('You can\'t unlock what isn\'t locked.\n-Richard Stallman\'s Fart', delete_after=3.0)
            return

        # If here then the channel is locked and we can proceed 
        
        # Get the Minions role
        MINIONS_ROLE = discord.utils.get(ctx.guild.roles, name='Minions')
        logger.info('[Mod unlock()] minion role found: {}'.format(MINIONS_ROLE.id))

        # Set the permissions
        logger.info('[Mod unlock()] editing {} permissions'.format(channel))
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await channel.set_permissions(MINIONS_ROLE, overwrite=None)

        # Tell the channel
        logger.info('[Mod unlock()] unlock message sent to {}'.format(channel))
        eObj = em(description='This channel is now unlocked, feel free to blah blah bl...', author=ctx.author.display_name, avatar=ctx.author.avatar_url, footer='Moderator action') 
        await ctx.send(embed=eObj)

        # Tell council
        logger.info('[Mod unlock()] council informed of locked channel')
        council = discord.utils.get(ctx.guild.channels, name='council')
        eObj = em(description='{} unlock {}'.format(ctx.message.author, channel.mention), footer='Moderator action')
        await ctx.send(embed=eObj)

def setup(bot):
    bot.add_cog(Mod(bot))
