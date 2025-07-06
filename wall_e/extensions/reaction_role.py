import asyncio
import discord
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class ReactionRole(commands.Cog):

    l_reaction_roles = {} # message_id : { emoji_id : role_id, ... }

    def __init__(self):
        log_info = Loggers.get_logger(logger_name='ReactionRole')
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[ReactionRole __init__()] initializing ReactionRole")
        self.guild: discord.Guild | None = None
        self.CHANNEL_PROMPT = "Hi \N{WAVING HAND SIGN}! Which channel would you like the message to be in?"
        self.TITLE_PROMPT = "What would you like the message title to say?"
        self.COLOUR_PROMPT = (
            "Would you like a custom colour for the message? Respond with a hex code or `none` to skip.\n"
            "**Need helping picking a color?** Check out: <https://htmlcolorcodes.com/>"
            )
        self.ROLE_PROMPT = (
            "Time to add roles"
            "The format to enter roles is emoji then the name of the role or its @. When you're done, type `done`\n"
            "**Example**\n```:snake: python-gang\n:stallman: @FOSS```"
            "Custom server emoji's are supported. "
        )

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "reaction_role_debug"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path, "reaction_role_warn"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "reaction_role_error"
        )

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info('[ReactionRole load()] loading mod channel')
        mod_channel_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger,
            self.guild,
            wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            'council'
        )
        self.mod_channel = discord.utils.get(self.guild.channels, id=mod_channel_id)

    @commands.Cog.listener('on_raw_reaction_add')
    @commands.Cog.listener('on_raw_reaction_remove')
    async def react(self, payload: discord.RawReactionActionEvent):
        """Handles adding/removing a role from user that reacts to a reaction role message"""
        if payload.user_id == bot.user.id: return
        if payload.message_id not in ReactionRole.l_reaction_roles.keys(): return

        emoji = payload.emoji
        emoji = str(emoji.id) if emoji.id else emoji.name

        if payload.event_type == 'REACTION_ADD':
            user = payload.member
            action = user.add_roles
            action_str = 'given to'
        else:
            user = self.guild.get_member(payload.user_id)
            action = user.remove_roles
            action_str = 'removed from'

        try:
            role = discord.utils.get(
                self.guild.roles,
                id= ReactionRole.l_reaction_roles[payload.message_id][emoji]
            )
            await action(role)
            self.logger.info(f'[ReactionRole react()] role @{role} was {action_str} {user}')
        except KeyError: return
        except discord.Forbidden:
            await self.mod_channel.send('I can\'t give out roles. Someone look at my permissions.')
            self.logger.info('[ReactionRole load()] Permissions error. Mods notified')

    async def request(self, ctx, prompt='', case_sensitive=False, timeout=60.0):
        """Sends an optional prompt and retrieves a response"""
        input_check = lambda msg: msg.channel == ctx.channel and msg.author == ctx.author

        if prompt: await ctx.send(prompt)
        msg = await bot.wait_for('message', check=input_check, timeout=timeout)
        response = msg.content
        if response.lower() == 'exit': raise Exception('exit')
        return response if case_sensitive else response.lower(), msg

    @commands.command(aliases=['rr'])
    async def reactionrole(self, ctx):
        self.logger.info("[ReactionRole reactionrole()] starting interactive process to create a reaction role embed")

        try:
            await ctx.send("Let's get started. **Type `exit` anytime during the process to stop.**")

            # Get channel
            channel, _ = await self.request(ctx, self.CHANNEL_PROMPT)
            try:
                channel = await commands.TextChannelConverter().convert(ctx, channel)
            except Exception:
                self.logger.info(f"[ReactionRole reactionrole()] channel {channel} not found")
                await ctx.send(f"Channel {channel} not found")
                raise commands.CommandError("Channel not found")

            if not channel.permissions_for(self.guild.me).send_messages:
                self.logger.info(f'[ReactionRole reactionrole()] Error: no send permission in {channel}')
                await ctx.send(f'I dont\'t have send permissions in {channel.mention}')
                raise commands.CommandError('No channel send permission')

            self.logger.info(f'[ReactionRole reactionrole()] channel for reaction role confirmed: {channel}')
            await ctx.send(f'Alright, channel set to {channel.mention}')

            # Get title
            title, _ = await self.request(ctx, self.TITLE_PROMPT, case_sensitive=True)
            self.logger.info(f'[ReactionRole reactionrole()] react role title set to: {title}')

            # Get colour
            colour, _ = await self.request(ctx, self.COLOUR_PROMPT)
            colour = colour.lower();
            if colour == 'none':
                colour = discord.Colour.darker_grey()
            else:
                try:
                    colour = await commands.ColorConverter().convert(ctx, f'#{colour[-6:]}')
                except Exception:
                    self.logger.info(f"[ReactionRole reactionrole()] Unrecognized user provided colour, using default value")
                    colour = discord.Colour.darker_grey()
                    await ctx.send("Can't find that colour. Going with the default")
            await ctx.send(f"Colour set to: https://singlecolorimage.com/get/{colour.value:x}/50x50")

            # Get emojis & roles
            await ctx.send(self.ROLE_PROMPT)
            emoji_role_ids = {}
            rr_text = []
            emojis = []
            while True:
                er, msg = await self.request(ctx, case_sensitive=True)
                if er.lower() == 'done': break
                er = er.split(' ')
                [emoji, role] = er[0], er[-1]
                try:
                    role = await commands.RoleConverter().convert(ctx, role)
                    emoji = await commands.PartialEmojiConverter().convert(ctx, emoji)
                except Exception as e:
                    if isinstance(e, commands.PartialEmojiConversionFailure) and not emoji.isalnum():
                        # Unicode emoji
                        emoji = discord.PartialEmoji(name=emoji)
                    else:
                        await msg.add_reaction('\N{CROSS MARK}')
                        error = f'Role {role}' if isinstance(e, commands.RoleNotFound) else f'Emoji {emoji}'
                        await ctx.send(f'{error} not found.')
                        continue

                # Permission check, can bot assign this role
                if role > self.guild.me.top_role:
                    await msg.add_reaction('\N{CROSS MARK}')
                    await ctx.send(f"The role {role} is higher than my highest role, so I cannot assign it")
                    continue

                # Duplicate check
                emoji_id = str(emoji.id) if emoji.is_custom_emoji() else emoji.name
                if emoji.id in emoji_role_ids.keys() or role.id in emoji_role_ids.values():
                    await msg.add_reaction('\N{BLACK QUESTION MARK ORNAMENT}')
                    await ctx.send(f'{emoji} and/or {role.mention} is already bound in this reaction role')
                    continue

                # Feedback for emoji - role added
                await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')

                # Update stuff
                emojis.append(emoji)
                rr_text.append(f'{emoji} {role.mention}')
                emoji_role_ids.update({emoji_id : role.id})
        except Exception as e:
            e_type = type(e)
            if e_type is asyncio.TimeoutError:
                self.logger.info("[ReactionRole reactionrole()] Command timed out")
                await ctx.send('You timed out. \N{WAVING HAND SIGN}')
            elif e_type is commands.CommandError:
                pass
            elif str(e) == 'exit':
                self.logger.info('[ReactionRole reactionrole()] User terminated command')
                await ctx.send('Goodbye \N{WAVING HAND SIGN}')
                return
            else:
                self.logger.info("[ReactionRole reactionrole()] Unknown exception encountered. Command terminated")
                raise e
            self.logger.info('[ReactionRole reactionrole()] Command terminated')
            await ctx.send('Redo command to try again.')
            return

        # Check for empty reaction role
        if len(emojis) == 0:
            await ctx.send('Can\'t create empty reaction role.')
            raise commands.CommandError('No emoji roles for the embed')

        # Construct reaction role
        em = await embed(
            self.logger,
            ctx,
            title=title,
            description='\n'.join(rr_text),
            colour=colour,
            footer_text='Self Assignable Roles'
        )
        if not em:
            await ctx.send('Embed creation failed. Might have too many emoji roles or the title is too long')
            return

        # Add emoji reactions
        react_msg = await channel.send(embed=em)
        for emoji in emojis:
            await react_msg.add_reaction(emoji)

        # Update local
        ReactionRole.l_reaction_roles.update({react_msg.id : emoji_role_ids})

        # Notify reaction role created
        await ctx.send(f'Here is your reaction role {react_msg.jump_url}')


async def setup(bot):
    await bot.add_cog(ReactionRole())
