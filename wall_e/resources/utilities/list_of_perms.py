# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions
import inspect


async def get_list_of_user_permissions(logger, ctx, user_id=None):
    """
    Geting a list of a user's permissions
    :param logger: the calling service's logger object
    :param ctx: the ctx object that is in dot command's parameters
    :param user_id: the ID of the user whose permission to get if its not just contaiend in ctx.author
    :return: the list of user's perms
    """
    author = ctx.author if user_id is None else ctx.guild.get_member(user_id)
    perms = [perm[0] for perm in inspect.getmembers(author.guild_permissions)
             if not perm[0].startswith('_') and not inspect.ismethod(perm[1]) and perm[1]]
    logger.info(
        f"[list_of_perms.py get_list_of_user_permissions()] permissions for {ctx.guild.get_member(user_id)}"
        f" is {perms}"
    )
    return perms


async def get_list_of_user_permissions_for_intentions(logger, interaction, user_id=None):
    """
    Geting a list of a user's permissions
    :param logger: the calling service's logger object
    :param interaction: the interaction object that is in slash command's parameters
    :param user_id: the ID of the user whose permission to get if its not just contaiend in interaction.author
    :return: the list of user's perms
    """
    author = interaction.user if user_id is None else interaction.guild.get_member(user_id)
    perms = [perm[0] for perm in author.guild_permissions if perm[1]]
    logger.info(
        f"[list_of_perms.py get_list_of_user_permissions_for_intentions ()] permissions for {author} is {perms}"
    )
    return perms
