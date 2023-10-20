import asyncio
from operator import itemgetter

import discord
from discord import app_commands
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.paginate import paginate_embed
from utilities.role_commands_autocomplete_functions import get_roles_with_members, get_assigned_roles, \
    get_assignable_roles, get_roles_that_can_be_deleted
from utilities.setup_logger import Loggers


def user_can_manage_roles(ctx: discord.Interaction) -> bool:
    return ctx.user.guild_permissions.administrator or ctx.user.guild_permissions.manage_roles


class RoleCommands(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="RoleCommands")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[RoleCommands __init__()] initializing RoleCommands")
        self.guild = None
        self.bot_channel = None
        self.exec_role_colour = [3447003, 6533347]

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path,
                "role_commands_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
                "role_commands_warn"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path,
                "role_commands_error"
            )

    @commands.Cog.listener(name="on_ready")
    async def get_bot_general_channel(self):
        while self.guild is None:
            await asyncio.sleep(2)
        reminder_chan_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            "role_commands"
        )
        self.bot_channel = discord.utils.get(
            self.guild.channels, id=reminder_chan_id
        )
        self.logger.debug(f"[RoleCommands get_bot_general_channel()] bot channel {self.bot_channel} acquired.")

    @app_commands.command(name="newrole", description="creates assignable role with the specified name")
    @app_commands.describe(new_role_name="name for assignable role to create")
    async def newrole(self, interaction: discord.Interaction, new_role_name: str):
        self.logger.info(f"[RoleCommands newrole()] {interaction.user} "
                         f"called newrole with following argument: new_role_name={new_role_name}")
        new_role_name = new_role_name.lower()
        guild = interaction.guild
        role_already_exists = len([role for role in guild.roles if role.name == new_role_name]) > 0
        if role_already_exists:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Role '{new_role_name}' exists. Calling "
                            f".iam {new_role_name} will add you to it."
            )
            if e_obj is not False:
                await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
                self.logger.debug(f"[RoleCommands newrole()] {new_role_name} already exists")
            return
        role = await guild.create_role(name=new_role_name)
        await role.edit(mentionable=True)
        self.logger.debug(f"[RoleCommands newrole()] {new_role_name} created and is set to mentionable")

        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user,
            description=(
                "You have successfully created role "
                f"**`{new_role_name}`**.\nCalling `.iam {new_role_name}` will add it to you."
            )
        )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @app_commands.command(name="deleterole", description="deletes empty assignable role with the specified name")
    @app_commands.describe(empty_role="name for empty assignable role to remove")
    @app_commands.autocomplete(empty_role=get_roles_that_can_be_deleted)
    async def deleterole(self, interaction: discord.Interaction, empty_role: str):
        self.logger.info(f"[RoleCommands deleterole()] {interaction.user} "
                         f"called deleterole with role {empty_role}.")
        if empty_role == "-1":
            return
        if not empty_role.isdigit():
            self.logger.debug(f"[RoleCommands deleterole()] invalid empty_role id of {empty_role} exists")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{empty_role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(empty_role))
        if role is None:
            self.logger.debug(f"[RoleCommands deleterole()] invalid role id of {empty_role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{empty_role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        await role.delete()
        self.logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user,
            description=f"Role **`{role}`** deleted."
        )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @app_commands.command(name="iam", description="add yourself to an assignable role")
    @app_commands.describe(role_to_assign_to_me="name for existing role to assign to yourself")
    @app_commands.autocomplete(role_to_assign_to_me=get_assignable_roles)
    async def iam(self, interaction: discord.Interaction, role_to_assign_to_me: str):
        self.logger.info(f"[RoleCommands iam()] {interaction.user} called iam with role {role_to_assign_to_me}")
        if role_to_assign_to_me == "-1":
            return
        if not role_to_assign_to_me.isdigit():
            self.logger.info(f"[RoleCommands iam()] invalid role id of {role_to_assign_to_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{role_to_assign_to_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role_to_assign_to_me))
        if role is None:
            self.logger.info(f"[RoleCommands iam()] invalid role id of {role_to_assign_to_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{role_to_assign_to_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        user = interaction.user
        await user.add_roles(role)
        self.logger.info(f"[RoleCommands iam()] user {user} added to role {role}.")
        if role == 'froshee':
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=(
                    "**WELCOME TO SFU!!!!**\nYou have successfully "
                    f"been added to role **`{role}`**."
                )
            )
        else:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"You have successfully been added to role **`{role}`**."
            )
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @app_commands.command(name="iamn", description="remove yourself from an assignable role")
    @app_commands.describe(role_to_remove_from_me="name for existing role to remove from yourself")
    @app_commands.autocomplete(role_to_remove_from_me=get_assigned_roles)
    async def iamn(self, interaction: discord.Interaction, role_to_remove_from_me: str):
        self.logger.info(
            f"[RoleCommands iamn()] {interaction.user} called iamn with role {role_to_remove_from_me}"
        )
        if role_to_remove_from_me == "-1":
            return
        if not role_to_remove_from_me.isdigit():
            self.logger.info(f"[RoleCommands iamn()] invalid role id of {role_to_remove_from_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{role_to_remove_from_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role_to_remove_from_me))
        if role is None:
            self.logger.info(f"[RoleCommands iamn()] invalid role id of {role_to_remove_from_me} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{role_to_remove_from_me}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction)
            return
        user = interaction.user
        await user.remove_roles(role)
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=interaction.client.user,
            description=f"You have successfully been removed from role **`{role}`**."
        )
        if e_obj is not False:
            self.logger.info(f"[RoleCommands iamn()] {user} has been removed from role {role}")
        await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)
        # delete role if last person
        members_of_role = role.members
        if not members_of_role:
            await role.delete()
            self.logger.info("[RoleCommands iamn()] no members were detected, role has been deleted.")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Role **`{role.name}`** deleted."
            )
            await self.send_message_to_user_or_bot_channel(e_obj, interaction=interaction)

    @app_commands.command(name="whois", description="list folks in a role")
    @app_commands.describe(role="name of the existing role to return the membership of")
    @app_commands.autocomplete(role=get_roles_with_members)
    async def whois(self, interaction: discord.Interaction, role: str):
        if role == "-1":
            return
        if not role.isdigit():
            try:
                await interaction.response.defer()
            except discord.errors.NotFound:
                await interaction.channel.send(
                    "Feeling a bit overloaded at the moment...Please try again in a few minutes"
                )
                return
            self.logger.info(f"[RoleCommands whois()] invalid role id of {role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid role **`{role}`** specified. Please select from the list."
            )
            await self.send_message_to_user_or_bot_channel(
                e_obj, interaction=interaction, send_func=interaction.followup.send
            )
            return
        role = discord.utils.get(interaction.guild.roles, id=int(role))
        if role is None:
            self.logger.info(f"[RoleCommands whois()] invalid role id of {role} detected")
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
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
                f"[RoleCommands whois()] {interaction.user} called whois with role "
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
            self.logger.info(f"[RoleCommands whois()] following members were found in the role: {log_string}")

            title = f"Members belonging to role: `{role}`"
            await paginate_embed(
                self.logger, bot, member_string, title=title, interaction=interaction
            )

    @app_commands.command(
        name="roles_assignable", description="will display all the self-assignable roles that exist"
    )
    async def roles(self, interaction: discord.Interaction):
        if interaction.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(interaction=interaction)
        else:
            number_of_roles_per_page = 5
            self.logger.info(f"[RoleCommands roles()] roles command detected from user {interaction.user}")

            # declares and populates self_assign_roles with all self-assignable roles and
            # how many people are in each role
            self_assign_roles = []
            for role in interaction.guild.roles:
                if role.name != "@everyone" and role.name[0] == role.name[0].lower():
                    number_of_members = len(discord.utils.get(interaction.guild.roles, name=str(role.name)).members)
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
                self.logger, bot, description_to_embed, "Self-Assignable Roles", interaction=interaction
            )

    @app_commands.command(
        name="roles",
        description="will display all the Mod/Exec/XP Assigned roles that exist"
    )
    async def Roles(self, interaction: discord.Interaction): # noqa N802
        if interaction.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(interaction=interaction)
        else:
            number_of_roles_per_page = 5
            self.logger.info(f"[RoleCommands Roles()] roles command detected from user {interaction.user}")

            # declares and populates assigned_roles with all self-assignable roles and
            # how many people are in each role
            assigned_roles = []
            for role in interaction.guild.roles:
                if role.name != "@everyone" and role.name[0] != role.name[0].lower():
                    number_of_members = len(discord.utils.get(interaction.guild.roles, name=str(role.name)).members)
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
                self.logger, bot, description_to_embed, "Mod/Exec/XP Assigned Roles", interaction=interaction
            )

    @app_commands.command(name="purgeroles", description="deletes all empty self-assignable roles")
    @app_commands.check(user_can_manage_roles)
    async def purgeroles(self, interaction: discord.Interaction):
        if interaction.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(interaction=interaction)
        else:
            await interaction.response.defer()
            self.logger.info(
                "[RoleCommands purgeroles()] "
                f"purgeroles command detected from user {interaction.user}"
            )

            embed = discord.Embed(type="rich")
            embed.color = discord.Color.blurple()
            embed.set_footer(text="brenfan", icon_url="https://i.imgur.com/vlpCuu2.jpg")

            # getting member instance of the bot
            bot_user = interaction.guild.get_member(interaction.client.user.id)

            # determine if bot is able to delete the roles
            sorted_list_of_authors_roles = sorted(bot_user.roles, key=lambda x: int(x.position), reverse=True)
            bot_highest_role = sorted_list_of_authors_roles[0]

            if not (bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator):
                embed.title = "It seems that the bot don't have permissions to delete roles. :("
                await self.send_message_to_user_or_bot_channel(
                    embed, interaction=interaction, send_func=interaction.followup.send
                )
                return
            self.logger.info(
                "[RoleCommands purgeroles()] bot's "
                f"highest role is {bot_highest_role} and its ability to delete roles is "
                f"{bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator}"
            )

            # determine if user who is calling the command is able to delete the roles
            sorted_list_of_authors_roles = sorted(interaction.user.roles, key=lambda x: int(x.position), reverse=True)
            author_highest_role = sorted_list_of_authors_roles[0]

            user_can_delete_roles = (
                interaction.user.guild_permissions.manage_roles or interaction.user.guild_permissions.administrator
            )
            if not user_can_delete_roles:
                embed.title = "You don't have permissions to delete roles. :("
                await self.send_message_to_user_or_bot_channel(
                    embed, interaction=interaction, send_func=interaction.followup.send
                )
                return

            self.logger.info(
                "[RoleCommands purgeroles()] user's "
                f"highest role is {author_highest_role} and its ability to delete roles is {user_can_delete_roles}"
            )

            guild = interaction.guild
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
                await self.send_message_to_user_or_bot_channel(
                    embed, interaction=interaction, send_func=interaction.followup.send
                )
                return
            deleted.sort(key=itemgetter(0))
            description = "\n".join(deleted)
            embed.title = f"Purging {len(deleted)} empty roles!"

            embed.description = description
            await self.send_message_to_user_or_bot_channel(
                embed, interaction=interaction, send_func=interaction.followup.send
            )

    async def send_message_to_user_or_bot_channel(self, e_obj, interaction=None, send_func=None):
        send_func = send_func if send_func is not None else interaction.response.send_message
        if e_obj is not False:
            if interaction.channel.id == self.bot_channel.id:
                self.logger.info("[RoleCommands send_message_to_user_or_bot_channel()] sending result to"
                                 " the bot channel ")
                await send_func(embed=e_obj)
            else:
                description = (
                    e_obj.description + f'\n\n\nPlease call the command {interaction.command.name} from the channel '
                                        f"[#{self.bot_channel.name}](https://discord.com/channels/"
                                        f"{interaction.guild.id}/{self.bot_channel.id}) to "
                                        f'avoid getting this warning'
                )
                e_obj = await embed(
                    self.logger,
                    interaction=interaction,
                    title='ATTENTION:',
                    colour=WallEColour.ERROR,
                    author=interaction.client.user,
                    description=description
                )
                if e_obj is not False:
                    self.logger.info(
                        "[RoleCommands send_message_to_user_or_bot_channel()] DMing the result to the user")
                    try:
                        await interaction.user.send(embed=e_obj)
                    except discord.errors.Forbidden:
                        await self.bot_channel.send(f'<@{interaction.user.id}>', embed=e_obj)

    async def send_error_message_to_user_for_paginated_commands(self, interaction=None):
        if interaction.user.dm_channel is None:
            send_func = (await interaction.user.create_dm()).send
        else:
            send_func = interaction.user.dm_channel.send
        description = (f'Please call the command `{interaction.command.name}` from the channel '
                       f"[#{self.bot_channel.name}](https://discord.com/channels/"
                       f"{interaction.guild_id}/{self.bot_channel.id}) to be able to use this command")
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            title='ATTENTION:',
            colour=WallEColour.ERROR,
            description=description,
            author=interaction.client.user,
        )
        if e_obj is not False:
            await send_func(embed=e_obj)
            self.logger.info(
                "[RoleCommands send_error_message_to_user_for_paginated_commands()] "
                f"embed sent to member {interaction.user}"
            )


async def setup(bot):
    await bot.add_cog(RoleCommands())
