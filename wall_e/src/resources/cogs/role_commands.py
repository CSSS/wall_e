from discord.ext import commands
import discord
import logging
from resources.utilities.paginate import paginate_embed
from resources.utilities.embed import embed
from operator import itemgetter

logger = logging.getLogger('wall_e')


def get_class_name():
    return "RoleCommands"


class RoleCommands(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    @commands.command()
    async def newrole(self, ctx, role_to_add):
        logger.info("[RoleCommands newrole()] {} "
                    "called newrole with following argument: role_to_add={}".format(ctx.message.author, role_to_add))
        role_to_add = role_to_add.lower()
        guild = ctx.guild
        for role in guild.roles:
            if role.name == role_to_add:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description="Role '{}' exists. Calling "
                                ".iam {} will add you to it.".format(role_to_add, role_to_add)
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
                    logger.info("[RoleCommands newrole()] {} already exists".format(role_to_add))
                return
        role = await guild.create_role(name=role_to_add)
        await role.edit(mentionable=True)
        logger.info("[RoleCommands newrole()] {} created and is set to mentionable".format(role_to_add))

        e_obj = await embed(
            ctx,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=(
                "You have successfully created role "
                "**`{}`**.\nCalling `.iam {}` will add it to you.".format(role_to_add, role_to_add)
            )
        )
        if e_obj is not False:
            await ctx.send(embed=e_obj)

    @commands.command()
    async def deleterole(self, ctx, role_to_delete):
        logger.info("[RoleCommands deleterole()] {} "
                    "called deleterole with role {}.".format(ctx.message.author, role_to_delete))
        role_to_delete = role_to_delete.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_delete)
        if role is None:
            logger.info("[RoleCommands deleterole()] role that user wants to delete doesnt seem to exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Role **`{}`** does not exist.".format(role_to_delete)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
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
                description="Role **`{}`** deleted.".format(role_to_delete)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
        else:
            logger.info("[RoleCommands deleterole()] members were detected, role can't be deleted.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Role **`{}`** has members. Cannot delete.".format(role_to_delete)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def iam(self, ctx, role_to_add):
        logger.info("[RoleCommands iam()] {} called iam with role {}".format(ctx.message.author, role_to_add))
        role_to_add = role_to_add.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_add)
        if role is None:
            logger.info("[RoleCommands iam()] role doesnt exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Role **`{}**` doesn't exist.\nCalling .newrole {}".format(role_to_add, role_to_add)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        user = ctx.message.author
        members_of_role = role.members
        if user in members_of_role:
            logger.info("[RoleCommands iam()] {} was already in the role {}.".format(user, role_to_add))
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Beep Boop\n You've already got the role dude STAAAHP!!"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
        else:
            await user.add_roles(role)
            logger.info("[RoleCommands iam()] user {} added to role {}.".format(user, role_to_add))

            if(role_to_add == 'froshee'):
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=(
                        "**WELCOME TO SFU!!!!**\nYou have successfully "
                        "been added to role **`{}`**.".format(role_to_add)
                    )
                )
            else:
                e_obj = await embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description="You have successfully been added to role **`{}`**.".format(role_to_add)
                )
            if e_obj is not False:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def iamn(self, ctx, role_to_remove):
        logger.info("[RoleCommands iamn()] {} called iamn with role {}".format(ctx.message.author, role_to_remove))
        role_to_remove = role_to_remove.lower()
        role = discord.utils.get(ctx.guild.roles, name=role_to_remove)
        if role is None:
            logger.info("[RoleCommands iamn()] role doesnt exist.")
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Role **`{}`** doesn't exist.".format(role_to_remove)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        members_of_role = role.members
        user = ctx.message.author
        if user in members_of_role:
            await user.remove_roles(role)
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="You have successfully been removed from role **`{}`**.".format(role_to_remove)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
                logger.info("[RoleCommands iamn()] {} has been removed from role {}".format(user, role_to_remove))
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
                    description="Role **`{}`** deleted.".format(role.name)
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
        else:
            logger.info("[RoleCommands iamn()] {} wasnt in the role {}".format(user, role_to_remove))
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="Boop Beep??\n You don't have the role, so how am I gonna remove it????"
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def whois(self, ctx, role_to_check):
        number_of_users_per_page = 20
        logger.info("[RoleCommands whois()] {} called whois with role {}".format(ctx.message.author, role_to_check))
        member_string = [""]
        log_string = ""
        role = discord.utils.get(ctx.guild.roles, name=role_to_check)
        if role is None:
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="**`{}`** does not exist.".format(role_to_check)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            logger.info("[RoleCommands whois()] role {} doesnt exist".format(role_to_check))
            return
        members_of_role = role.members
        if not members_of_role:
            logger.info("[RoleCommands whois()] there are no members in the role {}".format(role_to_check))
            e_obj = await embed(
                ctx,
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description="No members in role **`{}`**.".format(role_to_check)
            )
            if e_obj is not False:
                await ctx.send(embed=e_obj)
            return
        x, current_index = 0, 0
        for members in members_of_role:
            name = members.display_name
            member_string[current_index] += "{}\n".format(name)
            x += 1
            if x == number_of_users_per_page:
                member_string.append("")
                current_index += 1
                x = 0
            log_string += '{}\t'.format(name)
        logger.info("[RoleCommands whois()] following members were found in the role: {}".format(log_string))
        await paginate_embed(
            self.bot,
            ctx,
            self.config,
            member_string,
            title="Members belonging to role: `{0}`".format(role_to_check)
        )

    @commands.command()
    async def roles(self, ctx):
        number_of_roles_per_page = 5
        logger.info("[RoleCommands roles()] roles command detected from user {}".format(ctx.message.author))

        # declares and populates self_assign_roles with all self-assignable roles and how many people are in each role
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
                        "len(description_to_embed)={} "
                        "current_index={}".format(len(description_to_embed), current_index))
            description_to_embed[current_index] += "{} - {}\n".format(roles[0], roles[1])
            x += 1
            if x == number_of_roles_per_page:  # this determines how many entries there will be per page
                description_to_embed.append("Roles - Number of People in Role\n")
                current_index += 1
                x = 0
        logger.info("[RoleCommands roles()] transfer successful")

        await paginate_embed(self.bot, ctx, self.config, description_to_embed, title="Self-Assignable Roles")

    @commands.command()
    async def Roles(self, ctx):  # noqa: N802
        number_of_roles_per_page = 5
        logger.info("[RoleCommands Roles()] roles command detected from user {}".format(ctx.message.author))

        # declares and populates assigned_roles with all self-assignable roles and how many people are in each role
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
            description_to_embed[current_index] += "{} - {}\n".format(roles[0], roles[1])
            x += 1
            if x == number_of_roles_per_page:
                description_to_embed.append("Roles - Number of People in Role\n")
                current_index += 1
                x = 0
        logger.info("[RoleCommands Roles()] transfer successful")

        await paginate_embed(self.bot, ctx, self.config, description_to_embed, title="Mod/Exec/XP Assigned Roles")

    @commands.command()
    async def purgeroles(self, ctx):
        logger.info("[RoleCommands purgeroles()] purgeroles command detected from user {}".format(ctx.message.author))

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
            await ctx.send(embed=embed)
            return
        logger.info(
            "[RoleCommands purgeroles()] bot's "
            "highest role is {} and its ability to "
            "delete roles is {}".format(
                bot_highest_role,
                bot_user.guild_permissions.manage_roles or bot_user.guild_permissions.administrator
            )
        )

        # determine if user who is calling the command is able to delete the roles
        sorted_list_of_authors_roles = sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
        author_highest_role = sorted_list_of_authors_roles[0]

        if not (ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator):
            embed.title = "You don't have permissions to delete roles. :("
            await ctx.send(embed=embed)
            return
        logger.info(
            "[RoleCommands purgeroles()] user's "
            "highest role is {} and its ability to delete roles is {}".format(
                author_highest_role,
                ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator
            )
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
        logger.info("[RoleCommands purgeroles()] the ones it can't are: {}".format(', '.join(undeletable_roles)))

        deleted = []
        for role in soft_roles:
            members_in_role = role.members
            if not members_in_role:
                logger.info("[RoleCommands purgeroles()] deleting empty role @{}".format(role.name))
                deleted.append(role.name)
                await role.delete()
                logger.info("[RoleCommands purgeroles()] deleted empty role @{}".format(role.name))

        if not deleted:
            embed.title = "No empty roles to delete."
            await ctx.send(embed=embed)
            return
        deleted.sort(key=itemgetter(0))
        description = "\n".join(deleted)
        embed.title = "Purging {} empty roles!".format(len(deleted))

        embed.description = description

        await ctx.send(embed=embed)
