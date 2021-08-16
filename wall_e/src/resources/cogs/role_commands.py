import asyncio

from discord.ext import commands
import discord
import logging
from resources.utilities.paginate import paginate_embed
from resources.utilities.embed import embed
from operator import itemgetter

logger = logging.getLogger('wall_e')


class RoleCommands(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot_channel = None
        self.bot.loop.create_task(self.get_bot_general_channel())

    @commands.command()
    async def newrole(self, ctx, role_to_add):
        logger.info(f"[RoleCommands newrole()] {ctx.message.author} "
                    f"called newrole with following argument: role_to_add={role_to_add}")
        role_to_add = role_to_add.lower()
        guild = ctx.guild
        for role in guild.roles:
            if role.name == role_to_add:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"Role '{role_to_add}' exists. Calling "
                                f".iam {role_to_add} will add you to it."
                )
                await self.send_message_to_user_or_bot_channel(ctx, e_obj)
                if e_obj is not False:
                    logger.info(f"[RoleCommands newrole()] {role_to_add} already exists")
                return
        role = await guild.create_role(name=role_to_add)
        await role.edit(mentionable=True)
        logger.info(f"[RoleCommands newrole()] {role_to_add} created and is set to mentionable")

        e_obj = await embed(
            ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=(
                "You have successfully created role "
                f"**`{role_to_add}`**.\nCalling `.iam {role_to_add}` will add it to you."
            )
        )
        await self.send_message_to_user_or_bot_channel(ctx, e_obj)

    @commands.command()
    async def deleterole(self, ctx, role_to_delete):
        logger.info(f"[RoleCommands deleterole()] {ctx.message.author} "
                    f"called deleterole with role {role_to_delete}.")
        role_to_delete = role_to_delete.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_delete)
        if role is None:
            logger.info("[RoleCommands deleterole()] role that user wants to delete doesnt seem to exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Role **`{role_to_delete}`** does not exist."
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
            return
        members_of_role = role.members
        if not members_of_role:
            # deleteRole = await role.delete()
            await role.delete()
            logger.info("[RoleCommands deleterole()] no members were detected, role has been deleted.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Role **`{role_to_delete}`** deleted."
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
        else:
            logger.info("[RoleCommands deleterole()] members were detected, role can't be deleted.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Role **`{role_to_delete}`** has members. Cannot delete."
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)

    @commands.command()
    async def iam(self, ctx, role_to_add):
        logger.info(f"[RoleCommands iam()] {ctx.message.author} called iam with role {role_to_add}")
        role_to_add = role_to_add.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_add)
        if role is None:
            logger.info("[RoleCommands iam()] role doesnt exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Role **`{role_to_add}**` doesn't exist.\nCalling .newrole {role_to_add}"
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
            return
        user = ctx.message.author
        members_of_role = role.members
        if user in members_of_role:
            logger.info(f"[RoleCommands iam()] {user} was already in the role {role_to_add}.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Beep Boop\n You've already got the role dude STAAAHP!!"
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
        else:
            await user.add_roles(role)
            logger.info(f"[RoleCommands iam()] user {user} added to role {role_to_add}.")

            if (role_to_add == 'froshee'):
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=(
                        "**WELCOME TO SFU!!!!**\nYou have successfully "
                        f"been added to role **`{role_to_add}`**."
                    )
                )
            else:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"You have successfully been added to role **`{role_to_add}`**."
                )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)

    @commands.command()
    async def iamn(self, ctx, role_to_remove):
        logger.info(f"[RoleCommands iamn()] {ctx.message.author} called iamn with role {role_to_remove}")
        role_to_remove = role_to_remove.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_remove)
        if role is None:
            logger.info("[RoleCommands iamn()] role doesnt exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Role **`{role_to_remove}`** doesn't exist."
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
            return
        members_of_role = role.members
        user = ctx.message.author
        if user in members_of_role:
            await user.remove_roles(role)
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"You have successfully been removed from role **`{role_to_remove}`**."
            )
            if e_obj is not False:
                logger.info(f"[RoleCommands iamn()] {user} has been removed from role {role_to_remove}")
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)
            # delete role if last person
            members_of_role = role.members
            if not members_of_role:
                # deleteRole = await role.delete()
                await role.delete()
                logger.info("[RoleCommands iamn()] no members were detected, role has been deleted.")
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"Role **`{role.name}`** deleted."
                )
                await self.send_message_to_user_or_bot_channel(ctx, e_obj)
        else:
            logger.info(f"[RoleCommands iamn()] {user} wasnt in the role {role_to_remove}")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Boop Beep??\n You don't have the role, so how am I gonna remove it????"
            )
            await self.send_message_to_user_or_bot_channel(ctx, e_obj)

    async def send_message_to_user_or_bot_channel(self, ctx, e_obj):
        if e_obj is not False:
            if ctx.channel.id == self.bot_channel.id:
                logger.info("[RoleCommands send_message_to_user_or_bot_channel()] sending result to"
                            " the bot channel ")
                await ctx.send(embed=e_obj)
            else:
                try:
                    logger.info("[RoleCommands send_message_to_user_or_bot_channel()] attempting to "
                                "delete the message that invoked the command from outside the bot "
                                "specific channel ")
                    await ctx.message.delete()
                except discord.errors.NotFound:
                    logger.info("[RoleCommands send_message_to_user_or_bot_channel()] it appears the message "
                                "was already deleted")
                description = (
                        e_obj.description + f'\n\n\nPlease call the command {ctx.command.name} from the channel '
                                            f"[#{self.bot_channel.name}](https://discord.com/channels/"
                                            f"{ctx.guild.id}/{self.bot_channel.id}) to "
                                            f'avoid getting this warning'
                )
                e_obj = await embed(
                    ctx,
                    title='ATTENTION:',
                    colour=0xff0000,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=description
                )
                if e_obj is not False:
                    logger.info("[RoleCommands send_message_to_user_or_bot_channel()] DMing the result to the user")
                    await ctx.author.send(embed=e_obj)

    @commands.command()
    async def whois(self, ctx, role_to_check):
        if f"{role_to_check}" == "Muted" and ctx.message.author not in \
          discord.utils.get(ctx.guild.roles, name="Minions").members:
            await ctx.send("no peaking at the muted folks!")
            return
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx)
        else:
            number_of_users_per_page = 20
            logger.info(
                f"[RoleCommands whois()] {ctx.message.author} called whois with role "
                f"{role_to_check}"
            )
            member_string = [""]
            log_string = ""
            role = discord.utils.get(ctx.guild.roles, name=role_to_check)
            if role is None:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"**`{role_to_check}`** does not exist."
                )
                await self.send_message_to_user_or_bot_channel(ctx, e_obj)
                logger.info(f"[RoleCommands whois()] role {role_to_check} doesnt exist")
                return
            members_of_role = role.members
            if not members_of_role:
                logger.info(f"[RoleCommands whois()] there are no members in the role {role_to_check}")
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"No members in role **`{role_to_check}`**."
                )
                await self.send_message_to_user_or_bot_channel(ctx, e_obj)
                return
            x, current_index = 0, 0
            for members in members_of_role:
                name = members.display_name
                member_string[current_index] += f"{name}\n"
                x += 1
                if x == number_of_users_per_page:
                    member_string.append("")
                    current_index += 1
                    x = 0
                log_string += f'{name}\t'
            logger.info(f"[RoleCommands whois()] following members were found in the role: {log_string}")

            title = f"Members belonging to role: `{role_to_check}`"
            await paginate_embed(self.bot, ctx, self.config, member_string, title=title)

    @commands.command()
    async def roles(self, ctx):
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx)
        else:
            number_of_roles_per_page = 5
            logger.info(f"[RoleCommands roles()] roles command detected from user {ctx.message.author}")

            # declares and populates self_assign_roles with all self-assignable roles and
            # how many people are in each role
            self_assign_roles = []
            for role in ctx.guild.roles:
                if role.name != "@everyone" and role.name[0] == role.name[0].lower():
                    number_of_members = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                    self_assign_roles.append((str(role.name), number_of_members))

            logger.info("[RoleCommands roles()] self_assign_roles array populated with the roles extracted from "
                        "\"guild.roles\"")

            self_assign_roles.sort(key=itemgetter(0))
            logger.info("[RoleCommands roles()] roles in arrays sorted alphabetically")

            logger.info("[RoleCommands roles()] tranferring array to description array")
            x, current_index = 0, 0
            description_to_embed = ["Roles - Number of People in Role\n"]
            for roles in self_assign_roles:
                logger.info("[RoleCommands roles()] "
                            f"len(description_to_embed)={len(description_to_embed)} "
                            f"current_index={current_index}")
                description_to_embed[current_index] += f"{roles[0]} - {roles[1]}\n"
                x += 1
                if x == number_of_roles_per_page:  # this determines how many entries there will be per page
                    description_to_embed.append("Roles - Number of People in Role\n")
                    current_index += 1
                    x = 0
            logger.info("[RoleCommands roles()] transfer successful")
            await paginate_embed(self.bot, ctx, self.config, description_to_embed, "Self-Assignable Roles")

    @commands.command()
    async def Roles(self, ctx):  # noqa: N802
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx)
        else:
            number_of_roles_per_page = 5
            logger.info(f"[RoleCommands Roles()] roles command detected from user {ctx.message.author}")

            # declares and populates assigned_roles with all self-assignable roles and
            # how many people are in each role
            assigned_roles = []
            for role in ctx.guild.roles:
                if role.name != "@everyone" and role.name[0] != role.name[0].lower():
                    number_of_members = len(discord.utils.get(ctx.guild.roles, name=str(role.name)).members)
                    assigned_roles.append((str(role.name), number_of_members))

            logger.info("[RoleCommands Roles()] assigned_roles array populated with the roles extracted from "
                        "\"guild.roles\"")

            assigned_roles.sort(key=itemgetter(0))
            logger.info("[RoleCommands Roles()] roles in arrays sorted alphabetically")

            logger.info("[RoleCommands Roles()] tranferring array to description array")

            x, current_index = 0, 0
            description_to_embed = ["Roles - Number of People in Role\n"]
            for roles in assigned_roles:
                description_to_embed[current_index] += f"{roles[0]} - {roles[1]}\n"
                x += 1
                if x == number_of_roles_per_page:
                    description_to_embed.append("Roles - Number of People in Role\n")
                    current_index += 1
                    x = 0
            logger.info("[RoleCommands Roles()] transfer successful")
            await paginate_embed(self.bot, ctx, self.config, description_to_embed, "Mod/Exec/XP Assigned Roles")

    @commands.command()
    async def purgeroles(self, ctx):
        if ctx.channel.id != self.bot_channel.id:
            await self.send_error_message_to_user_for_paginated_commands(ctx)
        else:
            logger.info(
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
                await self.send_message_to_user_or_bot_channel(ctx, embed)

                return
            logger.info(
                "[RoleCommands purgeroles()] bot's "
                f"highest role is {bot_highest_role} and its ability to delete roles is "
                f"{bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator}"
            )

            # determine if user who is calling the command is able to delete the roles
            sorted_list_of_authors_roles = sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
            author_highest_role = sorted_list_of_authors_roles[0]

            if not (ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator):
                embed.title = "You don't have permissions to delete roles. :("
                await self.send_message_to_user_or_bot_channel(ctx, embed)
                return
            logger.info(
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
            logger.info("[RoleCommands purgeroles()] Located all the empty roles that both the user and the bot can "
                        "delete")
            logger.info(f"[RoleCommands purgeroles()] the ones it can't are: {', '.join(undeletable_roles)}")

            deleted = []
            for role in soft_roles:
                members_in_role = role.members
                if not members_in_role:
                    logger.info(f"[RoleCommands purgeroles()] deleting empty role @{role.name}")
                    deleted.append(role.name)
                    await role.delete()
                    logger.info(f"[RoleCommands purgeroles()] deleted empty role @{role.name}")

            if not deleted:
                embed.title = "No empty roles to delete."
                await self.send_message_to_user_or_bot_channel(ctx, embed)
                return
            deleted.sort(key=itemgetter(0))
            description = "\n".join(deleted)
            embed.title = f"Purging {len(deleted)} empty roles!"

            embed.description = description
            await self.send_message_to_user_or_bot_channel(ctx, embed)

    async def send_error_message_to_user_for_paginated_commands(self, ctx):
        await ctx.message.delete()
        description = (f'Please call the command `{ctx.command.name}` from the channel '
                       f"[#{self.bot_channel.name}](https://discord.com/channels/"
                       f"{ctx.guild.id}/{self.bot_channel.id}) to be able to use this command")
        e_obj = await embed(
            ctx.author,
            title='ATTENTION:',
            colour=0xff0000,
            description=description,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR')
        )
        if e_obj is not False:
            await ctx.author.send(embed=e_obj)
            logger.info(
                "[RoleCommands send_error_message_to_user_for_paginated_commands()] "
                f"embed sent to member {ctx.author}"
            )

    async def get_bot_general_channel(self):
        """
        gets the bot channel that the commands in the RoleCommands class are limited to operating in. Due to the fact
        that the reminder class was the first class to utilize that bot channel in a specific way and is already
        handling its detection and possible creation, the RoleCommands class will just wait approximately 100 seconds
        to give the reminder class a chance to create the bot channel before exiting if the RoleCommands class cannot
        find the bot channel.
        """
        await self.bot.wait_until_ready()
        bot_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')
        environment = self.config.get_config_value('basic_config', 'ENVIRONMENT')
        self.bot_channel = None
        if environment == 'PRODUCTION' or environment == 'LOCALHOST':
            logger.info(f"[RoleCommands get_bot_general_channel()] bot_channel_name set to {bot_channel_name} for "
                        f"environment {environment}")
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        elif environment == 'TEST':
            bot_channel_name = f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
            logger.info(f"[RoleCommands get_bot_general_channel()] bot_channel_name set to {bot_channel_name} for "
                        f"environment {environment}")
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        number_of_retries_to_attempt = 10
        number_of_retries = 0
        while self.bot_channel is None and number_of_retries < number_of_retries_to_attempt:
            logger.info("[RoleCommands get_bot_general_channel()] attempt "
                        f"({number_of_retries}/{number_of_retries_to_attempt}) for getting bot_channel ")
            await asyncio.sleep(10)
            number_of_retries += 1
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        if self.bot_channel is None:
            logger.info("[RoleCommands get_bot_general_channel()] ultimately unable to get the bot_channel. exiting "
                        "now.")
            await asyncio.sleep(20)  # this is just here so that the above log line gets a chance to get printed to
            # discord
            exit(1)
        logger.info("[RoleCommands get_bot_general_channel()] bot_channel acquired.")
