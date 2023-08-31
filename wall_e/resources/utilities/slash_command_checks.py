from collections import OrderedDict

import discord

from resources.utilities.config.config import WallEConfig
from resources.utilities.list_of_perms import get_list_of_user_permissions_for_intentions


async def slash_command_checks(logger, config: WallEConfig, interaction: discord.Interaction, help_dict: OrderedDict):
    """
    ensures that the slash commands are only run by users with access to the command and
     if its run in the TEST guild, that it's called in a correct channel
    :param logger: the calling service's logger object
    :param config: the WallEConfig object necessary to determine the correct channel names
     for processing slash command in the TEST guild
    :param interaction: the interaction object that is in the command's parameter for a slash command
    :param help_dict: needed to check the privilege level assigned to a slash command
    :return:
    """
    await command_in_correct_test_guild_channel(config, interaction)
    await _check_privilege(logger, help_dict, interaction)


async def command_in_correct_test_guild_channel(config: WallEConfig, interaction: discord.Interaction):
    """
    Ensures that the slash command is only processed if its in the correct channel in the TEST
     guild
    :param config: the WallEConfig object necessary to determine the correct channel names
     for processing slash command in the TEST guild
    :param interaction: the interaction object that is in the command's parameter
     for a slash command
    :return:
    """
    test_guild = config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST'
    correct_test_guild_text_channel = (
        interaction.guild is not None and
        (interaction.channel.name == f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
         or
         interaction.channel.name == config.get_config_value('basic_config', 'BRANCH_NAME').lower())
    )
    if not test_guild:
        return True
    if interaction.guild is None:
        return True
    if not correct_test_guild_text_channel:
        raise Exception("command called from wrong channel")


async def _check_privilege(logger, help_dict: OrderedDict, interaction: discord.Interaction):
    """
    Ensures that the slash command is called by someone whith access to it
    :param logger: the calling service's logger object
    :param help_dict: needed to check the privilege level assigned to a slash command
    :param interaction: the interaction object that is in the command's parameter for a slash command
    :return: True of user has access to the command and False otherwise
    """
    command_used = f"{interaction.command.name}"
    if command_used == "exit":
        return True
    if command_used not in help_dict:
        return False
    command_info = help_dict[command_used]
    if command_info['access'] == 'roles':
        if hasattr(interaction.user, "roles"):
            user = interaction.user
        else:
            user = [
                member for member in interaction.user.mutual_guilds[0].members
                if member.id == interaction.user.id
            ][0]
        user_roles = [
            role.name for role in sorted(user.roles, key=lambda x: int(x.position), reverse=True)
        ]
        shared_roles = set(user_roles).intersection(command_info['roles'])
        if len(shared_roles) == 0:
            await interaction.response.send_message(
                "You do not have adequate permission to execute this command, incident will be reported"
            )
        return len(shared_roles) > 0
    if command_info['access'] == 'permissions':
        user_perms = await get_list_of_user_permissions_for_intentions(logger, interaction)
        shared_perms = set(user_perms).intersection(command_info['permissions'])
        if len(shared_perms) == 0:
            await interaction.response.send_message(
                "You do not have adequate permission to execute this command, incident will be reported"
            )
        return len(shared_perms) > 0
    return False
