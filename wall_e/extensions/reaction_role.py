import asyncio
import discord
from discord.ext import commands


from utilities.global_vars import bot, wall_e_config
from wall_e_models.models import ReactRole

from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers
from typing import Union
import json


class ReactionRole(commands.Cog):

    l_reaction_roles = {}

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
            "The format to enter roles is emoji then the name of the role or its @, **space delimited**. "
            "When you're done, type `done`\n"
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

    @commands.Cog.listener('on_ready')
    async def load_reaction_roles(self):
        """Loads reaction roles from database"""
        react_roles = await ReactRole.get_all_message_ids_emoji_roles()
        for rr in react_roles:
            ReactionRole.l_reaction_roles[rr['message_id']] = json.loads(rr['emoji_roles_json'])
        self.logger.info(f'[ReactionRole load_reaction_roles()] Loaded {len(react_roles)} reaction role messages.')

    @commands.Cog.listener('on_raw_reaction_add')
    @commands.Cog.listener('on_raw_reaction_remove')
    async def react(self, payload: discord.RawReactionActionEvent):
        """Handles adding/removing a role from user that reacts to a reaction role message"""
        if payload.user_id == bot.user.id or payload.message_id not in ReactionRole.l_reaction_roles.keys():
            return

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
                id=ReactionRole.l_reaction_roles[payload.message_id][emoji]
            )
            await action(role)
            self.logger.info(f'[ReactionRole react()] role @{role} was {action_str} {user}')
        except KeyError:
            return
        except discord.Forbidden:
            await self.mod_channel.send('I can\'t give out roles. Someone look at my permissions.')
            self.logger.info('[ReactionRole load()] Permissions error. Mods notified')

    @commands.Cog.listener('on_raw_reaction_clear')
    @commands.Cog.listener('on_raw_reaction_clear_emoji')
    async def keep_reactions(self, payload: Union[discord.RawReactionClearEvent, discord.RawReactionClearEmojiEvent]):
        """Ensure react emojis from Wall-E are preserved on reaction role messages"""
        if payload.message_id not in ReactionRole.l_reaction_roles:
            return

        message_id = payload.message_id
        channel_id = await ReactRole.get_channel_id_by_message_id(message_id)
        message = await self.guild.get_channel(channel_id).fetch_message(message_id)
        if hasattr(payload, 'emoji'):
            # clear_emoji event
            emoji = payload.emoji
            emoji = str(emoji.id) if emoji.is_custom_emoji() else emoji.name
            if emoji in ReactionRole.l_reaction_roles[message.id].keys():
                await message.add_reaction(payload.emoji)
        else:
            # clear event
            emojis = ReactionRole.l_reaction_roles[payload.message_id].keys()
            emojis = [self.guild.get_emoji(int(em)) if em.isalnum() else em for em in emojis]
            for em in emojis:
                await message.add_reaction(em)

    async def request(self, ctx, prompt='', case_sensitive=False, timeout=60.0):
        """Sends an optional prompt and retrieves a response"""
        def input_check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        if prompt:
            await ctx.send(prompt)
        msg = await bot.wait_for('message', check=input_check, timeout=timeout)
        response = msg.content
        if response.lower() == 'exit':
            raise Exception('exit')
        return response if case_sensitive else response.lower(), msg

    async def get_emoji_role(self, ctx, emoji_role_ids, message=None, er_str=None):
        """Takes care of processing emoji role pair request and validation.
        If message and er_str are provided request is skip and validation begins."""
        if message is None:
            er, msg = await self.request(ctx, case_sensitive=True)
        else:
            er = er_str
            msg = message

        if er.lower() == 'done':
            return 'done'
        er = er.split(' ')
        emoji, role = er[0], er[-1]

        try:
            role = await commands.RoleConverter().convert(ctx, role)
            emoji = await commands.PartialEmojiConverter().convert(ctx, emoji)
        except Exception as e:
            if isinstance(e, commands.PartialEmojiConversionFailure) and not emoji[1:-1].isalnum():
                # Unicode emoji
                emoji = discord.PartialEmoji(name=emoji)
            else:
                await msg.add_reaction('\N{CROSS MARK}')
                error = f'Role {role}' if isinstance(e, commands.RoleNotFound) else f'Emoji {emoji}'
                await ctx.send(f'{error} not found.')
                return None

        # Permission check, can bot assign this role
        if role > self.guild.me.top_role:
            await msg.add_reaction('\N{CROSS MARK}')
            await ctx.send(f"The role {role} is higher than my highest role, so I cannot assign it")
            return None

        # Duplicate check
        if emoji.id in emoji_role_ids.keys() or role.id in emoji_role_ids.values():
            await msg.add_reaction('\N{BLACK QUESTION MARK ORNAMENT}')
            await ctx.send(f'{emoji} and/or {role.mention} is already bound in this reaction role')
            return None

        # Feedback for emoji - role added
        await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        return [emoji, role]

    async def rr_help(self, ctx: commands.Context, help_message=False):
        """Sends help message for react role command"""

        cmds = [
            ('Commands:', '', False),
            ('help', 'Shows this help message', False),
            ('make', 'Creates new react message', False),
            ('list', 'List of all react messages', False),
            ('edit <message_id> ', 'Add/remove an emoji role pair from an existing react message', False)
        ]
        em = await embed(
            logger=self.logger,
            ctx=ctx,
            title='Usage' if help_message else 'Error',
            description='Usage: .rr/reactionrole `cmd`',
            content=cmds,
            colour=discord.Colour.brand_green()
        )
        if not em:
            return

        self.logger.info('[ReactionRole rr_help()] Sending user help message')
        await ctx.send(embed=em)

    async def make(self, ctx: commands.Context):
        self.logger.info("[ReactionRole make()] starting interactive process to create a reaction role embed")

        try:
            await ctx.send("Let's get started. **Type `exit` anytime during the process to stop.**")

            # Get channel
            channel, _ = await self.request(ctx, self.CHANNEL_PROMPT)
            try:
                channel = await commands.TextChannelConverter().convert(ctx, channel)
            except Exception:
                self.logger.info(f"[ReactionRole make()] channel {channel} not found")
                await ctx.send(f"Channel {channel} not found")
                raise commands.CommandError("Channel not found")

            if not channel.permissions_for(self.guild.me).send_messages:
                self.logger.info(f'[ReactionRole make()] Error: no send permission in {channel}')
                await ctx.send(f'I dont\'t have send permissions in {channel.mention}')
                raise commands.CommandError('No channel send permission')

            self.logger.info(f'[ReactionRole make()] channel for reaction role confirmed: {channel}')
            await ctx.send(f'Alright, channel set to {channel.mention}')

            # Get title
            title, _ = await self.request(ctx, self.TITLE_PROMPT, case_sensitive=True)
            self.logger.info(f'[ReactionRole make()] react role title set to: {title}')

            # Get colour
            colour, _ = await self.request(ctx, self.COLOUR_PROMPT)
            if colour == 'none':
                colour = discord.Colour.darker_grey()
            else:
                try:
                    colour = await commands.ColorConverter().convert(ctx, f'#{colour[-6:]}')
                except Exception:
                    self.logger.info('[ReactionRole make()] Colour not found, using default value')
                    colour = discord.Colour.darker_grey()
                    await ctx.send('Can\'t find that colour. Going with the default')
            await ctx.send(f"Colour set to: https://singlecolorimage.com/get/{colour.value:x}/50x50")

            # Get emojis & roles
            await ctx.send(self.ROLE_PROMPT)
            emoji_role_ids = {}
            rr_text = []
            emojis = []
            while True:
                ret = await self.get_emoji_role(ctx, emoji_role_ids)
                if ret == 'done':
                    break
                if ret is None:
                    continue
                [emoji, role] = ret
                emoji_id = str(emoji.id) if emoji.is_custom_emoji() else emoji.name

                # Update stuff
                emojis.append(emoji)
                rr_text.append(f'{emoji} {role.mention}')
                emoji_role_ids.update({emoji_id: role.id})
        except Exception as e:
            e_type = type(e)
            if e_type is asyncio.TimeoutError:
                self.logger.info("[ReactionRole make()] Command timed out")
                await ctx.send('You timed out. \N{WAVING HAND SIGN}')
            elif str(e) == 'exit':
                self.logger.info('[ReactionRole make()] User terminated command')
                await ctx.send('Goodbye \N{WAVING HAND SIGN}')
                return
            elif e_type is commands.CommandError:
                pass
            else:
                self.logger.info("[ReactionRole make()] Unknown exception encountered. Command terminated")
                raise e
            self.logger.info('[ReactionRole make()] Command terminated')
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

        # Update database
        rr = ReactRole(
            channel_id=channel.id,
            message_id=react_msg.id,
            emoji_roles_json=json.dumps(emoji_role_ids)
        )
        await ReactRole.insert_react_role(rr)
        self.logger.info('[ReactionRole make()] created ReactRole')

        # Update local
        ReactionRole.l_reaction_roles.update({react_msg.id: emoji_role_ids})

        # Notify reaction role created
        await ctx.send(f'Here is your reaction role {react_msg.jump_url}')

    async def list_reaction_roles(self, ctx: commands.Context):
        """Lists all reaction roles in server"""
        self.logger.info('[ReactionRole list_reaction_roles()] Generating list of reaction roles')
        react_roles = await ReactRole.get_all_react_roles()
        content = []
        for rr in react_roles:
            emoji_roles = json.loads(rr.emoji_roles_json)
            channel = self.guild.get_channel(rr.channel_id)
            if channel is None:
                continue
            try:
                message = await channel.fetch_message(rr.message_id)
            except Exception:
                continue
            desc = []
            for emoji, role in emoji_roles.items():
                if emoji.isalnum():
                    emoji = self.guild.get_emoji(int(emoji))
                role = self.guild.get_role(role)
                desc.append(f'{emoji} {role.mention}')
            desc.append(message.jump_url)
            content.append([str(message.id), '\n'.join(desc)])

        em = await embed(
            self.logger,
            ctx,
            title='Reaction Roles',
            content=content,
            colour=discord.Colour.brand_green()
        )
        if em:
            await ctx.send(embed=em)
        self.logger.info('[ReactionRole list_reaction_roles()] List sent')

    async def edit(self, ctx: commands.Context, message_id):
        """Allows add/removing an emoji role pair to an existing reaction role message """
        self.logger.info('[ReactionRole edit()] Reaction role editing......')

        if int(message_id) not in ReactionRole.l_reaction_roles.keys():
            self.logger.info('[ReactionRole edit()] reaction role not found')
            await ctx.send('Can\'t find that reaction role. Make sure you have the correct message id')
            return

        rr = await ReactRole.get_react_role_by_message_id(message_id)
        channel = self.guild.get_channel(rr.channel_id)
        if channel is None:
            await ctx.send(f'Channel with id {rr.channel_id} not found. Channel might have been deleted.')
            return
        try:
            message = await channel.fetch_message(message_id)
        except discord.errors.NotFound:
            await ctx.send(f'Message with id {message_id} not found. The message might have been deleted.')
            return

        rr_embed = message.embeds[0]
        emoji_roles = json.loads(rr.emoji_roles_json)
        emojis = [self.guild.get_emoji(int(emoji)) if emoji.isalnum() else emoji for emoji in emoji_roles.keys()]
        roles = [self.guild.get_role(r) for r in emoji_roles.values()]
        add_emojis = []
        rm_emojis = []

        em = await embed(
            self.logger,
            ctx,
            title='Emoji role pairs',
            description='\n'.join([f'{emoji} {role.mention}' for emoji, role in zip(emojis, roles)]),
            colour=discord.Colour.brand_green(),
            footer_text=f'Message id: {message_id}'
        )
        if em:
            await ctx.send(embed=em)

        instructions = (
            'To add an emoji role pair put `add` followed by an emoji then the name of the role or its @, '
            '**space delimited**.\n'
            'To remove an emoji role pair put `rm` followed by the emoji from the pair.\n'
            '**Example**```Adding:\nadd :emoji: role\nadd :sfu: @role\nRemoving:\nrm :emoji:```'
            'Enter `done` when you\'re finished'
        )
        await ctx.send(instructions)
        self.logger.info('[ReactionRole edit()] Current emoji role pairs and instructions sent')
        while True:
            try:
                response, msg = await self.request(ctx, case_sensitive=True)
                if response.lower() == 'done':
                    break

                action, er_str = response.split(' ', 1)
                action = action.lower()
                if action == 'add':
                    self.logger.info('[ReactionRole edit()] Edit add action')
                    ret = await self.get_emoji_role(ctx, emoji_roles, msg, er_str)
                    if ret is None:
                        continue
                    [emoji, role] = ret
                    emoji_id = str(emoji.id) if emoji.is_custom_emoji() else emoji.name

                    # update stuff
                    self.logger.info(f'[ReactionRole edit()] Adding {emoji} - {role} pair')
                    emoji_roles[emoji_id] = role.id
                    emojis.append(emoji)
                    roles.append(role)
                    add_emojis.append(emoji)

                elif action == 'rm':
                    self.logger.info('[ReactionRole edit()] Edit remove action')
                    if er_str not in emoji_roles.keys():
                        await msg.add_reaction('\N{CROSS MARK}')
                        await ctx.send('Emoji not part of reaction role')
                        continue
                    if er_str[1:-1].isalnum():
                        emoji = await commands.PartialEmojiConverter().convert(ctx, er_str)
                        emoji_id = emoji.id
                    else:
                        emoji = er_str
                        emoji_id = emoji
                    role = self.guild.get_role(emoji_roles[emoji_id])

                    # update stuff
                    self.logger.info(f'[ReactionRole edit()] Removing {emoji} - {role} pair')
                    ret = emoji_roles.pop(emoji_id, None)
                    if ret is None:
                        raise Exception('something is wrong')
                    emojis.remove(emoji)
                    roles.remove(role)
                    rm_emojis.append(emoji)
                    await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                else:
                    self.logger.info('[ReactionRole edit()] Unknown edit action')
                    await ctx.send('Unknown edit action.')
            except asyncio.TimeoutError:
                self.logger.info('[ReactionRole edit()] Command timed out')
                await ctx.send('You timed out. \N{WAVING HAND SIGN}')
                return
            except commands.CommandError:
                pass
            except ValueError:
                self.logger.info('[ReactionRole edit()] Bad user input, we continue on')
                await msg.add_reaction('\N{BLACK QUESTION MARK ORNAMENT}')
                continue
            except Exception as e:
                if str(e) == 'exit':
                    self.logger.info('[ReactionRole edit()] User exit')
                    return
                if type(e) is ValueError:
                    pass
                raise e

        if len(add_emojis) <= 0 and len(rm_emojis) <= 0:
            self.logger.info('[ReactionRole edit()] Nothing to edit')
            return

        # Update class local
        ReactionRole.l_reaction_roles[message.id] = emoji_roles

        # Update db
        rr.emoji_roles_json = json.dumps(emoji_roles)
        await ReactRole.update_react_role(rr)

        # Update embed
        new_em = await embed(
            self.logger,
            ctx,
            title=rr_embed.title,
            description='\n'.join([f'{emoji} {role.mention}' for emoji, role in zip(emojis, roles)]),
            colour=rr_embed.colour,
            footer_text='Self Assignable Roles'
        )
        if new_em:
            await message.edit(embed=new_em)

        self.logger.info('[ReactionRole edit()] Removing emoji reactions')
        for emoji in rm_emojis:
            await message.clear_reaction(emoji)

        # Remove all non related emojis if new emojis to add
        if len(add_emojis) > 0:
            self.logger.info('[ReactionRole edit()] Removing unrelated reactions')
            message = await channel.fetch_message(message_id)
            current_emojis = [r.emoji for r in message.reactions]
            diff = set(current_emojis) - set(emojis)
            for emoji in diff:
                await message.clear_reaction(emoji)

        self.logger.info('[ReactionRole edit()] Adding new emoji reactions')
        for emoji in add_emojis:
            await message.add_reaction(emoji)

    @commands.command(aliases=['rr'])
    async def reactionrole(self, ctx, *subcommands):
        if not subcommands:
            self.logger.info("[ReactionRole reactionrole()] No subcommand")
            await self.rr_help(ctx)
            return

        cmd = subcommands[0].lower()
        if cmd == 'make':
            self.logger.info("[ReactionRole reactionrole()] make")
            await self.make(ctx)
        elif cmd == 'list':
            self.logger.info("[ReactionRole reactionrole()] list")
            await self.list_reaction_roles(ctx)
        elif cmd == 'edit':
            self.logger.info('[ReactionRole] edit')
            if len(subcommands) > 1:
                await self.edit(ctx, subcommands[1])
            else:
                self.logger.info('[ReactionRole] missing message id')
                await ctx.send('Missing message id')
                await self.rr_help(ctx)
        elif cmd == 'help':
            self.logger.info("[ReactionRole reactionrole()] help")
            await self.rr_help(ctx, True)
        else:
            self.logger.info(f"[ReactionRole reactionrole()] Unknown subcommand {subcommands}")
            await self.rr_help(ctx)


async def setup(bot):
    await bot.add_cog(ReactionRole())
