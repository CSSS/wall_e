import logging
from typing import List

import discord
from discord import app_commands


def get_lowercase_roles(interaction: discord.Interaction, current: str):
    """
    Gets the latest assign-able roles that contain the substring "current"
    :param interaction: the interaction object that contains the roles
    :param current: the substring that the user has entered into the search box on discord
    :return: the list of assign-able roles that match the substring "current"
    """
    print("getting the list of roles")
    roles = [
        role
        for role in list(interaction.guild.roles)
        if role.name[0] == role.name[0].lower() and current.lower() in role.name.lower() and
        role.name != "@everyone"
    ]
    print("list of roles obtained")
    return roles


async def get_assigned_or_unassigned_roles(
    interaction: discord.Interaction, current: str, error_message: List[str],
        assigned_roles=True) -> List[app_commands.Choice[str]]:
    """
    Get the assigned or unassigned roles for the user that is using /iam or /iamn
    :param interaction: the interaction object that contains the roles and the user using the command
    :param current: the substring that the user has entered into the search box on discord
    :param error_message: the list of error message to use
    0 -> If no assignable roles could be found that contain the "current" substring
    1 -> No assignable roles could be found
    2 -> If no assignable roles could be found that contain the "current" substring that the user does or
     does not have [dependent on assigned_roles Flag]
    3 -> If no assignable roles could be found that the user does or does not have [dependent on assigned_roles Flag]
    4-> string to place for the last element if there are more than 25 results
    :param assigned_roles: flag to indicate if the roles to get should be
    True -> roles that the user already has
    False -> roles that the user does not have
    :return: an array of the app_commands.Choices to return where the name is the name of the role and the value
     is the role's ID in string format
    cause an int version of the role ID was too big a number for discord to be able to handle
    """
    current = current.strip()
    roles = get_lowercase_roles(interaction, current)
    if len(roles) == 0:
        if len(current) > 0:
            roles = [app_commands.Choice(name=error_message[0], value="-1")]
        else:
            roles = [app_commands.Choice(name=error_message[1], value="-1")]
    else:
        roles = [
            app_commands.Choice(name=role.name, value=f"{role.id}")
            for role in roles if (
                role in interaction.user.roles if assigned_roles
                else role not in interaction.user.roles
            )
        ]
        if len(roles) == 0:
            if len(current) > 0:
                roles.append(
                    app_commands.Choice(name=error_message[2], value="-1"))
            else:
                roles.append(app_commands.Choice(name=error_message[3], value="-1"))
        if len(roles) > 25:
            roles = roles[:24]
            roles.append(app_commands.Choice(name=error_message[4], value="-1"))
    return roles


async def get_assignable_roles(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets the roles that the user can assign to themselves. Involved if the user uses /iam command
    :param interaction: the interaction object that contains the roles and the user using the command
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the role and the
     value is the role's ID in string format cause an int version of the role ID was too big a number for
     discord to be able to handle
    """
    await interaction.response.defer()
    error_message = [
        f'No assignable roles could be found that contain "{current}"',
        "No assignable roles could be found. Try the /sync_roles if you know it exists",
        f'You are in all the assignable roles that contain "{current}"',
        'You are in all the assignable roles',
        "Start typing to get better results"
    ]
    logger = logging.getLogger("RoleCommands")
    logger.debug(
        "[role_commands_autocomplete_functions.py get_assignable_roles()] getting list of assignable roles"
    )
    roles = await get_assigned_or_unassigned_roles(interaction, current, error_message, assigned_roles=False)
    logger.debug(
        "[role_commands_autocomplete_functions.py get_assignable_roles()] retrieved list of assignable roles"
    )
    return roles


async def get_assigned_roles(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets the roles that the user can remove from themselves. Involved if the user uses /iamn command
    :param interaction: the interaction object that contains the roles and the user using the command
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the role and the
     value is the role's ID in string format cause an int version of the role ID was too big a number for
     discord to be able to handle
    """
    await interaction.response.defer()
    error_message = [
        f'No assigned roles could be found that contain "{current}"',
        "No assigned roles could be found. Try the /sync_roles if you know it exists",
        f'You are not in any assignable roles that contain "{current}"',
        'You are not in any assignable roles',
        "Start typing to get better results"
    ]
    logger = logging.getLogger("RoleCommands")
    logger.debug(
        "[role_commands_autocomplete_functions.py get_assigned_roles()] getting list of assigned roles"
    )
    roles = await get_assigned_or_unassigned_roles(interaction, current, error_message)
    logger.debug(
        "[role_commands_autocomplete_functions.py get_assigned_roles()] retrieved list of assigned roles"
    )
    return roles


async def get_roles_that_can_be_deleted(interaction: discord.Interaction,
                                        current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of assign-able roles that a user can delete with /delete_role command
    :param interaction: the interaction object that contains the roles
    :param current: the substring that the user has entered into the search box on discord
    :return: an array of the app_commands.Choices to return where the name is the name of the role and the
     value is the role's ID in string format cause an int version of the role ID was too big a number for
     discord to be able to handle
    """
    await interaction.response.defer()
    current = current.strip()
    roles = get_lowercase_roles(interaction, current)
    roles = [
        app_commands.Choice(name=role.name, value=f"{role.id}")
        for role in roles
        if len(role.members) == 0
    ]
    if len(roles) == 0:
        if len(current) > 0:
            roles.append(
                app_commands.Choice(
                    name=f'No empty assignable roles could be found that contain "{current}"', value="-1"
                )
            )
        else:
            roles.append(
                app_commands.Choice(
                    name="No empty assignable roles could be found. Try the /sync_roles if you know it exists",
                    value="-1"
                )
            )
    if len(roles) > 25:
        roles = roles[:24]
        roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    logger.debug(
        "[role_commands_autocomplete_functions.py get_roles_that_can_be_deleted()] obtained list of "
        "roles that can be deleted"
    )
    return roles


async def get_roles_with_members(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Get a list of all the roles that have members where the user can use with the /whois command
    :param interaction: the interaction object that contains the roles
    :param current: the substring that the user has entered into the search box on discord
    :return:an array of the app_commands.Choices to return where the name is the name of the role and the
     value is the role's ID in string format cause an int version of the role ID was too big a number for
     discord to be able to handle
    """
    await interaction.response.defer()
    current = current.strip()
    print("getting list of all roles")
    roles = [
        app_commands.Choice(name=role.name, value=f"{role.id}")
        for role in list(interaction.guild.roles)
        if len(role.members) > 0 and role.name != "@everyone" and current.lower() in role.name.lower()
    ]
    print("list of all roles obtained")
    if len(roles) == 0:
        if len(current) > 0:
            roles.append(
                app_commands.Choice(
                    name=f'No roles could be found with a member that contain "{current}"', value="-1"
                )
            else:
                roles.append(
                    app_commands.Choice(
                        name="No roles could be found with a member. Try the /sync_roles if you know it exists",
                        value="-1"
                    )
                )
        if len(roles) > 25:
            roles = roles[:24]
            roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    logger.debug(
        "[role_commands_autocomplete_functions.py get_roles_with_members()] obtained list of "
        "roles with members"
    )
    return roles
