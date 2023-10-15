from typing import List

import discord
from discord import app_commands


from utilities.global_vars import wall_e_config
from utilities.wall_e_bot import extension_location_python_path


def user_has_permission_to_load_or_unload_extension(interaction, extension):
    """
    Indicates if the user has access to the specified extension

    :param interaction:  the interaction object that contains the roles
    :param extension: the name of the extension being loaded or unloaded
    :return: True or False to indicate if the user using a `load/unload/reload` has the rights to the
     specified extension
    """
    roles = [role.name for role in sorted(interaction.user.roles, key=lambda x: int(x.position), reverse=True)]
    user_is_bot_manager = 'Bot_manager' in roles
    user_is_moderator = 'Minions' in roles or 'Moderators' in roles
    valid_load_call = user_is_bot_manager or user_is_moderator \
        if extension in ['ban', 'mod'] else user_is_bot_manager
    return valid_load_call


async def get_extension_that_can_be_loaded(
        interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of extensions that a user can load with /load command

    :param interaction: the interaction object that contains the list of loaded extensions
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the class in the
     specified extension and the value is the name of the extension that can be passed to `bot.load_extension`
    """
    from extensions.administration import extension_mapping
    current = current.strip().lower()
    extensions = wall_e_config.get_extensions()
    loaded_extensions = list(interaction.client.extensions)
    extensions = [
        app_commands.Choice(
            name=extension_mapping[extension], value=f"{extension}"
        )
        for extension in extensions
        if f"{extension_location_python_path}{extension}" not in loaded_extensions and
        current in extension_mapping[extension].lower() and
        user_has_permission_to_load_or_unload_extension(interaction, extension)
    ]
    if len(extensions) == 0:
        if len(current) > 0:
            extensions.append(
                app_commands.Choice(
                    name=f'No unloaded extensions could be found that contain "{current}"', value="-1"
                )
            )
        else:
            extensions.append(app_commands.Choice(name="No unloaded extensions could be found", value="-1"))
    if len(extensions) > 25:
        extensions = extensions[:24]
        extensions.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return extensions


async def get_extension_that_can_be_unloaded(
        interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of extensions that a user can unload with /unload command

    :param interaction: the interaction object that contains the list of loaded extensions
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the class in the
     specified extension and the value is the name of the extension that can be passed to `bot.unload_extension`
    """
    from extensions.administration import extension_mapping
    current = current.strip().lower()
    extensions = wall_e_config.get_extensions()
    loaded_extensions = list(interaction.client.extensions)
    extensions = [
        app_commands.Choice(
            name=extension_mapping[extension], value=extension
        )
        for extension in extensions
        if f"{extension_location_python_path}{extension}" in loaded_extensions and
        current in extension_mapping[extension].lower() and
        user_has_permission_to_load_or_unload_extension(interaction, extension)
    ]
    if len(extensions) == 0:
        if len(current) > 0:
            extensions.append(
                app_commands.Choice(
                    name=f'No loaded extensions could be found that contain "{current}"', value="-1"
                )
            )
        else:
            extensions.append(app_commands.Choice(name="No loaded extensions could be found", value="-1"))
    if len(extensions) > 25:
        extensions = extensions[:24]
        extensions.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return extensions
