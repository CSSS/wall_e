# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions
import inspect

async def get_list_of_user_permissions(ctx, userID=False):
    if userID is not False:
        return [ perm[0] for perm in inspect.getmembers(ctx.guild.get_member(id).guild_permissions) if not perm[0].startswith('_') and not inspect.ismethod(perm[1]) and perm[1] == True]
    else:
        return [ perm[0] for perm in inspect.getmembers(ctx.author.guild_permissions) if not perm[0].startswith('_') and not inspect.ismethod(perm[1]) and perm[1] == True]
