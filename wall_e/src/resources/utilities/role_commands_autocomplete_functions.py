from typing import List

import discord
from discord import app_commands


def get_lowercase_roles(interaction: discord.Interaction, current: str):
    return [
        role
        for role in list(interaction.guild.roles)
        if role.name[0] == role.name[0].lower() and current.lower() in role.name.lower() and
        role.name != "@everyone"
    ]


async def get_assigned_or_unassigned_roles(
    interaction: discord.Interaction, current: str, error_message: List[str],
        assigned_roles=True) -> List[app_commands.Choice[str]]:
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
    error_message = [
        f'No assignable roles could be found that contain "{current}"',
        "No assignable roles could be found",
        f'You are in all the assignable roles that contain "{current}"',
        'You are in all the assignable roles',
        "Start typing to get better results"
    ]
    return await get_assigned_or_unassigned_roles(interaction, current, error_message, assigned_roles=False)


async def get_assigned_roles(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    error_message = [
        f'No assigned roles could be found that contain "{current}"',
        "No assigned roles could be found",
        f'You are not in any assignable roles that contain "{current}"',
        'You are not in any assignable roles',
        "Start typing to get better results"
    ]
    return await get_assigned_or_unassigned_roles(interaction, current, error_message)


async def get_roles_that_can_be_deleted(interaction: discord.Interaction,
                                        current: str) -> List[app_commands.Choice[str]]:
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
            roles.append(app_commands.Choice(name="No empty assignable roles could be found", value="-1"))
    if len(roles) > 25:
        roles = roles[:24]
        roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return roles


async def get_roles_with_members(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    current = current.strip()
    roles = [
        app_commands.Choice(name=role.name, value=f"{role.id}")
        for role in list(interaction.guild.roles)
        if len(role.members) > 0 and role.name != "@everyone" and current.lower() in role.name.lower()
    ]
    if len(roles) == 0:
        if len(current) > 0:
            roles.append(
                app_commands.Choice(
                    name=f'No roles could be found with a member that contain "{current}"', value="-1"
                )
            )
        else:
            roles.append(app_commands.Choice(name="No roles could be found with a member", value="-1"))
    if len(roles) > 25:
        roles = roles[:24]
        roles.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return roles
