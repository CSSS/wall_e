from typing import List

import discord
from discord import app_commands


from utilities.global_vars import wall_e_config


def user_has_permission_to_load_or_unload_cog(interaction, cog):
    """
    Indicates if the user has access to the specified cog

    :param interaction:  the interaction object that contains the roles
    :param cog: the cog dict that contains the name of the cog being loaded or unloaded
    :return: True or False to indicate if the user using a `load/unload/reload` has the rights to the specified cog
    """
    cog_name = cog['name']
    roles = [role.name for role in sorted(interaction.user.roles, key=lambda x: int(x.position), reverse=True)]
    user_is_bot_manager = 'Bot_manager' in roles
    user_is_moderator = 'Minions' in roles or 'Moderators' in roles
    valid_load_call = user_is_bot_manager or user_is_moderator \
        if cog_name in ['ban', 'mod'] else user_is_bot_manager
    return valid_load_call


async def get_cog_that_can_be_loaded(
        interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of cogs that a user can load with /load command

    :param interaction: the interaction object that contains the list of loaded extensions
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the class in the
     specified Cog and the value is the path to the cog that can be passed to `bot.load_extension`
    """
    from cogs.administration import extension_mapping
    current = current.strip()
    cogs = wall_e_config.get_cogs()
    loaded_extensions = list(list(interaction.client.extensions))
    cogs = [
        app_commands.Choice(
            name=extension_mapping[f"{cog['path']}{cog['name']}"], value=f"{cog['path']}{cog['name']}"
        )
        for cog in cogs
        if f"{cog['path']}{cog['name']}" not in loaded_extensions and
           current in extension_mapping[f"{cog['path']}{cog['name']}"] and
           user_has_permission_to_load_or_unload_cog(interaction, cog)
    ]
    if len(cogs) == 0:
        if len(current) > 0:
            cogs.append(
                app_commands.Choice(
                    name=f'No unloaded cogs could be found that contain "{current}"', value="-1"
                )
            )
        else:
            cogs.append(app_commands.Choice(name="No unloaded cogs could be found", value="-1"))
    if len(cogs) > 25:
        roles = cogs[:24]
        roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return cogs


async def get_cog_that_can_be_unloaded(
        interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of cogs that a user can unload with /unload command

    :param interaction: the interaction object that contains the list of loaded extensions
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the class in the
     specified Cog and the value is the path to the cog that can be passed to `bot.unload_extension`
    """
    from cogs.administration import extension_mapping
    current = current.strip()
    cogs = wall_e_config.get_cogs()
    loaded_extensions = list(list(interaction.client.extensions))
    cogs = [
        app_commands.Choice(
            name=extension_mapping[f"{cog['path']}{cog['name']}"], value=f"{cog['path']}{cog['name']}"
        )
        for cog in cogs
        if f"{cog['path']}{cog['name']}" in loaded_extensions and
           current in extension_mapping[f"{cog['path']}{cog['name']}"] and
           user_has_permission_to_load_or_unload_cog(interaction, cog)
    ]
    if len(cogs) == 0:
        if len(current) > 0:
            cogs.append(
                app_commands.Choice(
                    name=f'No loaded cogs could be found that contain "{current}"', value="-1"
                )
            )
        else:
            cogs.append(app_commands.Choice(name="No loaded cogs could be found", value="-1"))
    if len(cogs) > 25:
        roles = cogs[:24]
        roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return cogs
