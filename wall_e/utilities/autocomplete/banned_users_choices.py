from typing import List

import discord
from discord import app_commands


async def get_banned_users(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Gets a list of banned users that can be viewed with /bans

    :param interaction:
    :param current: the query for either a username or user id
    :return: an array of the app_commands.Choices to return where the name is the name of the banned username and the
     value is the corresponding user id
    """
    from extensions.ban import Ban
    current = current.lower()
    banned_users = [
        app_commands.Choice(name=f"{banned_user_name}({banned_user_id})", value=f"{banned_user_id}")
        for banned_user_id, banned_user_name in Ban.ban_list.items()
        if current in banned_user_name or current in f"{banned_user_id}"
    ]
    if len(banned_users) == 0:
        if len(current) > 0:
            banned_users = [
                app_commands.Choice(name=f"No banned users could be found that contain {current}", value="-1")
            ]
        else:
            banned_users = [
                app_commands.Choice(name="No banner user could be found", value="-1")
            ]
    if len(banned_users) > 25:
        banned_users = banned_users[:24]
        banned_users.append(app_commands.Choice(name="Start typing to get better results", value="-1"))
    return banned_users
