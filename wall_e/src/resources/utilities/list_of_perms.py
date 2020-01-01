# list of possible roles to check can be pulled from here
# https://discordpy.readthedocs.io/en/rewrite/api.html#discord.Permissions
import inspect

async def get_list_of_user_permissions(ctx, userID=False):
    if userID is not False:
        return [ attribute[0] for attribute in inspect.getmembers(ctx.guild.get_member(id).guild_permissions) if not attribute[0].startswith('_') and not inspect.ismethod(attribute[1]) and attribute[1] == True]
    else:
        return [ attribute[0] for attribute in inspect.getmembers(ctx.author.guild_permissions) if not attribute[0].startswith('_') and not inspect.ismethod(attribute[1]) and attribute[1] == True]
