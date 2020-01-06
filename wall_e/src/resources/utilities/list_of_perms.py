# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions
import inspect
import logging
logger = logging.getLogger('wall_e')


async def get_list_of_user_permissions(ctx, user_id=False):
    if user_id is not False:
        perms = [perm[0] for perm in inspect.getmembers(ctx.guild.get_member(user_id).guild_permissions)
                 if not perm[0].startswith('_') and not inspect.ismethod(perm[1]) and perm[1]]
        logger.info("[list_of_perms.py get_list_of_user_permissions()] permissions for {} is {}".format(
            ctx.guild.get_member(id), perms))
    else:
        perms = [perm[0] for perm in inspect.getmembers(ctx.author.guild_permissions)
                 if not perm[0].startswith('_') and not inspect.ismethod(perm[1]) and perm[1]]
        logger.info("[list_of_perms.py get_list_of_user_permissions()] permissions for {} is {}".format(
            ctx.author, perms))
    return perms
