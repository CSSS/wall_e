import asyncio
from operator import itemgetter

import discord
from discord import app_commands
from discord.ext import commands

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.paginate import paginate_embed
from utilities.role_commands_autocomplete_functions import get_roles_with_members, get_assigned_roles, \
    get_assignable_roles, get_roles_that_can_be_deleted
from utilities.setup_logger import Loggers


def user_can_manage_roles(ctx):
    return ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_roles


class RoleCommands(commands.Cog):

    def __init__(self, bot, config, bot_channel_manager):
        log_info = Loggers.get_logger(logger_name="RoleCommands")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.config = config
        self.guild = None
        self.bot_channel = None
        self.exec_role_colour = [3447003, 6533347]
        self.bot_channel_manager = bot_channel_manager

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path,
                "role_commands_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path,
                "role_commands_error"
            )

    @commands.Cog.listener(name="on_ready")
    async def get_bot_general_channel(self):
        while self.guild is None:
            await asyncio.sleep(2)
        reminder_chan_id = await self.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, self.config.get_config_value('basic_config', 'ENVIRONMENT'),
            "role_commands"
        )
        self.bot_channel = discord.utils.get(
            self.guild.channels, id=reminder_chan_id
        )
        self.logger.info(f"[RoleCommands get_bot_general_channel()] bot channel {self.bot_channel} acquired.")

    @app_commands.command(name="newrole", description="creates assignable role with the specified name")
    @app_commands.describe(new_role_name="name for assignable role to create")
    async def slash_newrole(self, interaction: discord.Interaction, new_role_name: str):
        self.logger.info(f"[RoleCommands slash_newrole()] {interaction.user} "
                         f"called newrole with following argument: new_role_name={new_role_name}")
        new_role_name = new_role_name.lower()
        guild = interaction.guild
        role_already_exists = len([role for role in guild.roles if role.name == new_role_name]) > 0
        if role_already_exists:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Role '{new_role_name}' exists. Calling "
                            f".iam {new_role_name} will add you to it."
            )
            if e_obj is not False:
                await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
                self.logger.info(f"[RoleCommands slash_newrole()] {new_role_name} already exists")
            return
        role = await guild.create_role(name=new_role_name)
        await role.edit(mentionable=True)
        self.logger.info(f"[RoleCommands slash_newrole()] {new_role_name} created and is set to mentionable")

        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user.display_name,
            avatar=interaction.client.user.display_avatar.url,
            description=(
                "You have successfully created role "
                f"**`{new_role_name}`**.\nCalling `.iam {new_role_name}` will add it to you."
            )
        )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @commands.command(
        brief="creates assignable role with the specified name",
        help=(
            'Arguments:\n'
            '---"new assignable role name": name for assignable role to add\n\n'
            'Example:\n'
            '---.newrole "role name"\n\n'
        ),
        usage='"new assignable role name"'
    )
    async def newrole(self, ctx, new_role_name):
        self.logger.info(f"[RoleCommands newrole()] {ctx.message.author} "
                         f"called newrole with following argument: new_role_name={new_role_name}")
        new_role_name = new_role_name.lower()
        guild = ctx.guild
        for role in guild.roles:
            if role.name == new_role_name:
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=f"Role '{new_role_name}' exists. Calling "
                                f".iam {new_role_name} will add you to it.\n\n"
                                f"PSST: try out the new `/newrole` command"
                                "\n`.newrole` will be deprecated soon."
                )
                await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
                if e_obj is not False:
                    self.logger.info(f"[RoleCommands newrole()] {new_role_name} already exists")
                return
        role = await guild.create_role(name=new_role_name)
        await role.edit(mentionable=True)
        self.logger.info(f"[RoleCommands newrole()] {new_role_name} created and is set to mentionable")

        e_obj = await embed(
            self.logger,
            colour=WallEColour.ERROR,
            ctx=ctx,
            author=ctx.me.display_name,
            avatar=ctx.me.display_avatar.url,
            description=(
                "You have successfully created role "
                f"**`{new_role_name}`**.\nCalling `.iam {new_role_name}` will add it to you."
                "\n\nPSST: try out the new `/newrole` command"
                "\n`.newrole` will be deprecated soon."
            )
        )
        await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)

    @app_commands.command(name="deleterole", description="deletes empty assignable role with the specified name")
    @app_commands.describe(empty_role="name for empty assignable role to remove")
    @app_commands.autocomplete(empty_role=get_roles_that_can_be_deleted)
    async def slash_deleterole(self, interaction: discord.Interaction, empty_role: str):
        self.logger.info(f"[RoleCommands slash_deleterole()] {interaction.user} "
                         f"called deleterole with role {empty_role}.")
        if empty_role == "-1":
            return
        if not empty_role.isdigit():
            self.logger.info(f"[RoleCommands slash_deleterole()] invalid empty_role id of {empty_role} exists")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{empty_role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(empty_role))
        if role is None:
            self.logger.info(f"[RoleCommands slash_deleterole()] invalid role id of {empty_role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{empty_role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        await role.delete()
        self.logger.info("[RoleCommands slash_deleterole()] no members were detected, role has been deleted.")
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user.display_name,
            avatar=interaction.client.user.display_avatar.url,
            description=f"Role **`{role}`** deleted."
        )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @commands.command(
        brief="deletes empty assignable role with the specified name",
        help=(
            'Arguments:\n'
            '---existing empty assignable role name: name for the existing empty assignable role to delete\n\n'
            'Example:\n'
            '---.deleterole "role name"\n\n'
        ),
        usage='"existing empty assignable role name"'
    )
    async def deleterole(self, ctx, role_to_delete):
        self.logger.info(f"[RoleCommands deleterole()] {ctx.message.author} "
                         f"called deleterole with role {role_to_delete}.")
        role_to_delete = role_to_delete.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_delete)
        if role is None:
            self.logger.info("[RoleCommands deleterole()] role that user wants to delete doesnt seem to exist.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"Role **`{role_to_delete}`** does not exist."
                    "\n\nPSST: try out the new `/deleterole` command"
                    "\n`.deleterole` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
            return
        members_of_role = role.members
        if not members_of_role:
            # deleteRole = await role.delete()
            await role.delete()
            self.logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"Role **`{role_to_delete}`** deleted."
                    "\n\nPSST: try out the new `/deleterole` command"
                    "\n`.deleterole` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
        else:
            self.logger.info("[RoleCommands deleterole()] members were detected, role can't be deleted.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"Role **`{role_to_delete}`** has members. Cannot delete."
                    "\n\nPSST: try out the new `/deleterole` command"
                    "\n`.deleterole` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)

    @app_commands.command(name="iam", description="add yourself to an assignable role")
    @app_commands.describe(role_to_assign_to_me="name for existing role to assign to yourself")
    @app_commands.autocomplete(role_to_assign_to_me=get_assignable_roles)
    async def slash_iam(self, interaction: discord.Interaction, role_to_assign_to_me: str):
        self.logger.info(f"[RoleCommands slash_iam()] {interaction.user} called iam with role {role_to_assign_to_me}")
        if role_to_assign_to_me == "-1":
            return
        if not role_to_assign_to_me.isdigit():
            self.logger.info(f"[RoleCommands slash_iam()] invalid role id of {role_to_assign_to_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role_to_assign_to_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role_to_assign_to_me))
        if role is None:
            self.logger.info(f"[RoleCommands slash_iam()] invalid role id of {role_to_assign_to_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role_to_assign_to_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        user = interaction.user
        await user.add_roles(role)
        self.logger.info(f"[RoleCommands slash_iam()] user {user} added to role {role}.")
        if role == 'froshee':
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=(
                    "**WELCOME TO SFU!!!!**\nYou have successfully "
                    f"been added to role **`{role}`**."
                )
            )
        else:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"You have successfully been added to role **`{role}`**."
            )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @commands.command(
        brief="add yourself to an assignable role",
        help=(
            'Arguments:\n'
            '---existing assignable role name: name for existing role to assign to yourself\n\n'
            'Example:\n'
            '---.iam "role name"\n\n'
        ),
        usage='"existing assignable role name"'
    )
    async def iam(self, ctx, role_to_add):
        self.logger.info(f"[RoleCommands iam()] {ctx.message.author} called iam with role {role_to_add}")
        role_to_add = role_to_add.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_add)
        if role is None:
            self.logger.info("[RoleCommands iam()] role doesnt exist.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"Role **`{role_to_add}`** doesn't exist.\nCalling .newrole {role_to_add}"
                    "\n\nPSST: try out the new `/iam` command"
                    "\n`.iam` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
            return
        user = ctx.message.author
        members_of_role = role.members
        if user in members_of_role:
            self.logger.info(f"[RoleCommands iam()] {user} was already in the role {role_to_add}.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    "Beep Boop\n You've already got the role dude STAAAHP!!"
                    "\n\nPSST: try out the new `/iam` command"
                    "\n`.iam` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
        else:
            await user.add_roles(role)
            self.logger.info(f"[RoleCommands iam()] user {user} added to role {role_to_add}.")

            if (role_to_add == 'froshee'):
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=(
                        "**WELCOME TO SFU!!!!**\nYou have successfully "
                        f"been added to role **`{role_to_add}`**."
                        "\n\nPSST: try out the new `/iam` command"
                        "\n`.iam` will be deprecated soon."
                    )
                )
            else:
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=(
                        f"You have successfully been added to role **`{role_to_add}`**."
                        "\n\nPSST: try out the new `/iam` command"
                        "\n`.iam` will be deprecated soon."
                    )
                )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)

    @app_commands.command(name="iamn", description="remove yourself from an assignable role")
    @app_commands.describe(role_to_remove_from_me="name for existing role to remove from yourself")
    @app_commands.autocomplete(role_to_remove_from_me=get_assigned_roles)
    async def slash_iamn(self, interaction: discord.Interaction, role_to_remove_from_me: str):
        self.logger.info(
            f"[RoleCommands slash_iamn()] {interaction.user} called iamn with role {role_to_remove_from_me}"
        )
        if role_to_remove_from_me == "-1":
            return
        if not role_to_remove_from_me.isdigit():
            self.logger.info(f"[RoleCommands slash_iamn()] invalid role id of {role_to_remove_from_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role_to_remove_from_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role_to_remove_from_me))
        if role is None:
            self.logger.info(f"[RoleCommands slash_iamn()] invalid role id of {role_to_remove_from_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role_to_remove_from_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        user = interaction.user
        await user.remove_roles(role)
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user.display_name,
            avatar=interaction.client.user.display_avatar.url,
            description=f"You have successfully been removed from role **`{role}`**."
        )
        if e_obj is not False:
            self.logger.info(f"[RoleCommands slash_iamn()] {user} has been removed from role {role}")
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
        # delete role if last person
        members_of_role = role.members
        if not members_of_role:
            await role.delete()
            self.logger.info("[RoleCommands slash_iamn()] no members were detected, role has been deleted.")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Role **`{role.name}`** deleted."
            )
            await self.send_message_to_user_or_bot_channel(
                e_obj, interaction=interaction, send_func=interaction.channel.send
            )

    @commands.command(
        brief="remove yourself from an assignable role",
        help=(
            'Arguments:\n'
            '---existing assigned role name: name for existing assigned role to remove from yourself\n\n'
            'Example:\n'
            '---.iamn "role name"\n\n'
        ),
        usage='"existing assigned role name"'
    )
    async def iamn(self, ctx, role_to_remove):
        self.logger.info(f"[RoleCommands iamn()] {ctx.message.author} called iamn with role {role_to_remove}")
        role_to_remove = role_to_remove.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_remove)
        if role is None:
            self.logger.info("[RoleCommands iamn()] role doesnt exist.")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"Role **`{role_to_remove}`** doesn't exist."
                    "\n\nPSST: try out the new `/iamn` command"
                    "\n`.iamn` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
            return
        members_of_role = role.members
        user = ctx.message.author
        if user in members_of_role:
            await user.remove_roles(role)
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    f"You have successfully been removed from role **`{role_to_remove}`**."
                    "\n\nPSST: try out the new `/iamn` command"
                    "\n`.iamn` will be deprecated soon."
                )
            )
            if e_obj is not False:
                self.logger.info(f"[RoleCommands iamn()] {user} has been removed from role {role_to_remove}")
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
            # delete role if last person
            members_of_role = role.members
            if not members_of_role:
                # deleteRole = await role.delete()
                await role.delete()
                self.logger.info("[RoleCommands iamn()] no members were detected, role has been deleted.")
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=(
                        f"Role **`{role.name}`** deleted."
                        "\n\nPSST: try out the new `/iamn` command"
                        "\n`.iamn` will be deprecated soon."
                    )
                )
                await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
        else:
            self.logger.info(f"[RoleCommands iamn()] {user} wasnt in the role {role_to_remove}")
            e_obj = await embed(
                self.logger,
                colour=WallEColour.ERROR,
                ctx=ctx,
                author=ctx.me.display_name,
                avatar=ctx.me.display_avatar.url,
                description=(
                    "Boop Beep??\n You don't have the role, so how am I gonna remove it????"
                    "\n\nPSST: try out the new `/iamn` command"
                    "\n`.iamn` will be deprecated soon."
                )
            )
            await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)

    async def send_message_to_user_or_bot_channel(self, e_obj, interaction=None, ctx=None, send_func=None):
        author = interaction.user if interaction is not None else ctx.author
        guild_id = interaction.guild.id if interaction is not None else ctx.guild.id
        cmd_name = interaction.command.name if interaction is not None else ctx.command.name
        message = ctx.message if ctx is not None else None
        channel_id = interaction.channel.id if interaction is not None else ctx.channel.id
        send_func = send_func if send_func is not None else \
            interaction.response.send_message if interaction is not None else ctx.send
        if interaction is None:
            bot_name = ctx.me.display_name
            bot_avatar = ctx.me.display_avatar.url
        else:
            bot_name = interaction.client.user.display_name
            bot_avatar = interaction.client.user.display_avatar.url
        if e_obj is not False:
            if channel_id == self.bot_channel.id:
                self.logger.info("[RoleCommands send_message_to_user_or_bot_channel()] sending result to"
                                 " the bot channel ")
                await send_func(embed=e_obj)
            else:
                try:
                    self.logger.info("[RoleCommands send_message_to_user_or_bot_channel()] attempting to "
                                     "delete the message that invoked the command from outside the bot "
                                     "specific channel ")
                    if message is not None:
                        await message.delete()
                except discord.errors.NotFound:
                    self.logger.info("[RoleCommands send_message_to_user_or_bot_channel()] it appears the message "
                                     "was already deleted")
                description = (
                    e_obj.description + f'\n\n\nPlease call the command {cmd_name} from the channel '
                                        f"[#{self.bot_channel.name}](https://discord.com/channels/"
                                        f"{guild_id}/{self.bot_channel.id}) to "
                                        f'avoid getting this warning'
                )
                e_obj = await embed(
                    self.logger,
                    ctx=ctx,
                    interaction=interaction,
                    title='ATTENTION:',
                    colour=WallEColour.ERROR,
                    author=bot_name,
                    avatar=bot_avatar,
                    description=description
                )
                if e_obj is not False:
                    self.logger.info(
                        "[RoleCommands send_message_to_user_or_bot_channel()] DMing the result to the user")
                    try:
                        await author.send(embed=e_obj)
                    except discord.errors.Forbidden:
                        await self.bot_channel.send(f'<@{author.id}>', embed=e_obj)

    @app_commands.command(name="whois", description="list folks in a role")
    @app_commands.describe(role="name of the existing role to return the membership of")
    @app_commands.autocomplete(role=get_roles_with_members)
    async def slash_whois(self, interaction: discord.Interaction, role: str):
        if role == "-1":
            return
        if not role.isdigit():
            await interaction.response.defer()
            self.logger.info(f"[RoleCommands slash_whois()] invalid role id of {role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(
                e_obj, interaction=interaction, send_func=interaction.followup.send
            )
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role))
        if role is None:
            self.logger.info(f"[RoleCommands slash_whois()] invalid role id of {role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user.display_name,
                avatar=interaction.client.user.display_avatar.url,
                description=f"Invalid role **`{role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        author_roles = [
            role.name for role in interaction.user.roles
        ]
        if role.name == "Muted" and "Minions" not in author_roles:
            await interaction.response.send_message("no peaking at the muted folks!")
            return
        if interaction.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(interaction=interaction)
        else:
            number_of_users_per_page = 20
            self.logger.info(
                f"[RoleCommands slash_whois()] {interaction.user} called whois with role "
                f"{role}"
            )
            member_string = [""]
            log_string = ""

            members_of_role = role.members
            x, current_index = 0, 0
            for members in members_of_role:
                name = members.display_name
                member_string[current_index] += f"{name}"
                exec_role = [
                    role for role in members.roles
                    if role.colour.value in self.exec_role_colour and role.name != "Execs"
                ]
                if len(exec_role) > 0:
                    member_string[current_index] += f"- {exec_role[0]}"
                member_string[current_index] += "\n"
                x += 1
                if x == number_of_users_per_page:
                    member_string.append("")
                    current_index += 1
                    x = 0
                log_string += f'{name}\t'
            self.logger.info(f"[RoleCommands slash_whois()] following members were found in the role: {log_string}")

            title = f"Members belonging to role: `{role}`"
            await paginate_embed(
                self.logger, self.bot, member_string, title=title, interaction=interaction
            )

    @commands.command(
        brief="list folks in a role",
        help=(
            'Arguments:\n'
            '---role to check: name of the existing role to return the membership of\n\n'
            'Example:\n'
            '---.whois "role name"\n\n'
        ),
        usage='"role to check"'
    )
    async def whois(self, ctx, role_to_check):
        author_is_minion = ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members
        if f"{role_to_check}" == "Muted" and not author_is_minion:
            await ctx.send(
                "no peaking at the muted folks!"
                "\n\nPSST: try out the new `/whois` command"
                "\n`.whois` will be deprecated soon."
            )
            return
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx=ctx)
        else:
            number_of_users_per_page = 10
            self.logger.info(
                f"[RoleCommands whois()] {ctx.message.author} called whois with role "
                f"{role_to_check}"
            )
            member_string = [""]
            log_string = ""
            role = discord.utils.get(ctx.guild.roles, name=role_to_check)
            if role is None:
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=(
                        f"**`{role_to_check}`** does not exist."
                        "\n\nPSST: try out the new `/whois` command"
                        "\n`.whois` will be deprecated soon."
                    )
                )
                await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
                self.logger.info(f"[RoleCommands whois()] role {role_to_check} doesnt exist")
                return
            members_of_role = role.members
            if not members_of_role:
                self.logger.info(f"[RoleCommands whois()] there are no members in the role {role_to_check}")
                e_obj = await embed(
                    self.logger,
                    colour=WallEColour.ERROR,
                    ctx=ctx,
                    author=ctx.me.display_name,
                    avatar=ctx.me.display_avatar.url,
                    description=(
                        f"No members in role **`{role_to_check}`**."
                        "\n\nPSST: try out the new `/whois` command"
                        "\n`.whois` will be deprecated soon."
                    )
                )
                await self.send_message_to_user_or_bot_channel(e_obj, ctx=ctx)
                return
            x, current_index = 0, 0

            for members in members_of_role:
                name = members.display_name
                member_string[current_index] += f"{name}"
                exec_role = [
                    role for role in members.roles
                    if role.colour.value in self.exec_role_colour and role.name != "Execs"
                ]
                if len(exec_role) > 0:
                    member_string[current_index] += f"- {exec_role[0]}"
                member_string[current_index] += "\n"
                x += 1
                if x == number_of_users_per_page:
                    member_string[current_index] += (
                        "\n\nPSST: try out the new `/whois` command"
                        "\n`.whois` will be deprecated soon."
                    )
                    member_string.append("")
                    current_index += 1
                    x = 0
                log_string += f'{name}\t'
            self.logger.info(f"[RoleCommands whois()] following members were found in the role: {log_string}")

            title = f"Members belonging to role: `{role_to_check}`"
            await paginate_embed(self.logger, self.bot, member_string, title=title, ctx=ctx)

    @commands.command(brief="will display all the self-assignable roles that exist")
    async def roles(self, ctx):
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx=ctx)
        else:
            number_of_roles_per_page = 5
            self.logger.info(f"[RoleCommands roles()] roles command detected from user {ctx.message.author}")

            # declares and populates self_assign_roles with all self-assignable roles and
            # how many people are in each role
            self_assign_roles = []
            for role in ctx.guild.roles:
                if role.name != "@everyone" and role.name[0] == role.name[0].lower():
                    number_of_members = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                    self_assign_roles.append((str(role.name), number_of_members))

            self.logger.info("[RoleCommands roles()] self_assign_roles array populated with the roles extracted from "
                             "\"guild.roles\"")

            self_assign_roles.sort(key=itemgetter(0))
            self.logger.info("[RoleCommands roles()] roles in arrays sorted alphabetically")

            self.logger.info("[RoleCommands roles()] tranferring array to description array")
            x, current_index = 0, 0
            description_to_embed = ["Roles - Number of People in Role\n"]
            for roles in self_assign_roles:
                self.logger.info("[RoleCommands roles()] "
                                 f"len(description_to_embed)={len(description_to_embed)} "
                                 f"current_index={current_index}")
                description_to_embed[current_index] += f"{roles[0]} - {roles[1]}\n"
                x += 1
                if x == number_of_roles_per_page:  # this determines how many entries there will be per page
                    description_to_embed.append("Roles - Number of People in Role\n")
                    current_index += 1
                    x = 0
            self.logger.info("[RoleCommands roles()] transfer successful")
            await paginate_embed(
                self.logger, self.bot, description_to_embed, "Self-Assignable Roles", ctx=ctx
            )

    @commands.command(brief="will display all the Mod/Exec/XP Assigned roles that exist")
    async def Roles(self, ctx):  # noqa: N802
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx=ctx)
        else:
            number_of_roles_per_page = 5
            self.logger.info(f"[RoleCommands Roles()] roles command detected from user {ctx.message.author}")

            # declares and populates assigned_roles with all self-assignable roles and
            # how many people are in each role
            assigned_roles = []
            for role in ctx.guild.roles:
                if role.name != "@everyone" and role.name[0] != role.name[0].lower():
                    number_of_members = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                    assigned_roles.append((str(role.name), number_of_members))

            self.logger.info("[RoleCommands Roles()] assigned_roles array populated with the roles extracted from "
                             "\"guild.roles\"")

            assigned_roles.sort(key=itemgetter(0))
            self.logger.info("[RoleCommands Roles()] roles in arrays sorted alphabetically")

            self.logger.info("[RoleCommands Roles()] tranferring array to description array")

            x, current_index = 0, 0
            description_to_embed = ["Roles - Number of People in Role\n"]
            for roles in assigned_roles:
                description_to_embed[current_index] += f"{roles[0]} - {roles[1]}\n"
                x += 1
                if x == number_of_roles_per_page:
                    description_to_embed.append("Roles - Number of People in Role\n")
                    current_index += 1
                    x = 0
            self.logger.info("[RoleCommands Roles()] transfer successful")
            await paginate_embed(
                self.logger, self.bot, description_to_embed, "Mod/Exec/XP Assigned Roles", ctx=ctx
            )

    @commands.command(brief="deletes all empty self-assignable roles")
    @commands.check(user_can_manage_roles)
    async def purgeroles(self, ctx):
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx=ctx)
        else:
            self.logger.info(
                "[RoleCommands purgeroles()] "
                f"purgeroles command detected from user {ctx.message.author}"
            )

            embed = discord.Embed(type="rich")
            embed.color = discord.Color.blurple()
            embed.set_footer(text="brenfan", icon_url="https://i.imgur.com/vlpCuu2.jpg")

            # getting member instance of the bot
            bot_user = ctx.guild.get_member(ctx.bot.user.id)

            # determine if bot is able to delete the roles
            sorted_list_of_authors_roles = sorted(bot_user.roles, key=lambda x: int(x.position), reverse=True)
            bot_highest_role = sorted_list_of_authors_roles[0]

            if not (bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator):
                embed.title = "It seems that the bot don't have permissions to delete roles. :("
                await self.send_message_to_user_or_bot_channel(embed, ctx=ctx)

                return
            self.logger.info(
                "[RoleCommands purgeroles()] bot's "
                f"highest role is {bot_highest_role} and its ability to delete roles is "
                f"{bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator}"
            )

            # determine if user who is calling the command is able to delete the roles
            sorted_list_of_authors_roles = sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
            author_highest_role = sorted_list_of_authors_roles[0]

            if not (ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator):
                embed.title = "You don't have permissions to delete roles. :("
                await self.send_message_to_user_or_bot_channel(embed, ctx=ctx)
                return
            self.logger.info(
                "[RoleCommands purgeroles()] user's "
                f"highest role is {author_highest_role} and its ability to delete roles is "
                f"{ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator}"
            )

            guild = ctx.guild
            soft_roles = []
            undeletable_roles = []
            for role in guild.roles:
                if role.name != "@everyone" and role.name == role.name.lower():
                    if author_highest_role >= role and bot_highest_role >= role:
                        soft_roles.append(role)
                    else:
                        undeletable_roles.append(role.name)
            self.logger.info(
                "[RoleCommands purgeroles()] Located all the empty roles that both the user and the bot can "
                "delete")
            self.logger.info(f"[RoleCommands purgeroles()] the ones it can't are: {', '.join(undeletable_roles)}")

            deleted = []
            for role in soft_roles:
                members_in_role = role.members
                if not members_in_role:
                    self.logger.info(f"[RoleCommands purgeroles()] deleting empty role @{role.name}")
                    deleted.append(role.name)
                    await role.delete()
                    self.logger.info(f"[RoleCommands purgeroles()] deleted empty role @{role.name}")

            if not deleted:
                embed.title = "No empty roles to delete."
                await self.send_message_to_user_or_bot_channel(embed, ctx=ctx)
                return
            deleted.sort(key=itemgetter(0))
            description = "\n".join(deleted)
            embed.title = f"Purging {len(deleted)} empty roles!"

            embed.description = description
            await self.send_message_to_user_or_bot_channel(embed, ctx=ctx)

    async def send_error_message_to_user_for_paginated_commands(self, ctx=None, interaction=None):
        if ctx is not None:
            await ctx.message.delete()
        elif interaction is not None:
            await interaction.message.delete()
        description = (f'Please call the command `{ctx.command.name}` from the channel '
                       f"[#{self.bot_channel.name}](https://discord.com/channels/"
                       f"{ctx.guild.id}/{self.bot_channel.id}) to be able to use this command")
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            interaction=interaction,
            title='ATTENTION:',
            colour=WallEColour.ERROR,
            description=description,
            author=interaction.client.user.display_name,
            avatar=interaction.client.user.display_avatar.url
        )
        if e_obj is not False:
            await ctx.author.send(embed=e_obj)
            self.logger.info(
                "[RoleCommands send_error_message_to_user_for_paginated_commands()] "
                f"embed sent to member {ctx.author}"
            )
