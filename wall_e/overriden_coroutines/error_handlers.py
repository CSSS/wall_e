import asyncio
import re

import discord
from discord.ext import commands

from cogs.manage_test_guild import ManageTestGuild


from utilities.embed import embed as imported_embed, WallEColour
from utilities.setup_logger import print_wall_e_exception


async def report_text_command_error(ctx, error):
    """
    Function that gets called when the script cant understand the command that the user invoked
    :param ctx: the ctx object that is part of command parameters that are not slash commands
    :param error: the error that was encountered
    :return:
    """
    from utilities.global_vars import logger
    correct_channel = ManageTestGuild.check_text_command_test_environment(ctx)
    if correct_channel:
        if isinstance(error, commands.errors.ArgumentParsingError):
            description = (
                f"Uh-oh, seem like you have entered a badly formed string and wound up with error:"
                f"\n'{error.args[0]}'\n\n[Technical Details link if you care to look]"
                f"(https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?"
                f"highlight=argumentparsingerror#exceptions)\n\n"
                f"**You have 20 seconds to copy your input to do a retry before "
                f"I ensure it is wiped from the channel**"
            )
            error_type = f"{type(error)}"[8:-2]
            embed_obj = await imported_embed(
                logger=ctx.cog.logger, ctx=ctx, title=f"Error {error_type} encountered",
                description=description, colour=WallEColour.ERROR
            )
            if embed_obj is not False:
                message = await ctx.channel.send(
                    embed=embed_obj
                )
                await asyncio.sleep(20)
                try:
                    await ctx.message.delete()
                except discord.errors.NotFound:
                    pass
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
        else:
            await report_command_errors(error, logger, ctx=ctx)


async def report_slash_command_error(interaction: discord.Interaction, error):
    """
    Function that gets called when the script cant understand the slash command that the user invoked
    :param interaction:
    :param error:
    :return:
    """
    from utilities.global_vars import logger
    await report_command_errors(error, logger, interaction=interaction)


async def report_command_errors(error, logger, interaction=None, ctx=None):
    privilege_errors = (
        discord.ext.commands.errors.MissingAnyRole, discord.ext.commands.errors.MissingRole,
        discord.ext.commands.errors.MissingPermissions, discord.app_commands.errors.MissingPermissions,
        discord.app_commands.errors.MissingRole, discord.app_commands.errors.MissingAnyRole,

    )
    if isinstance(error, privilege_errors):
        from utilities.global_vars import incident_report_logger
        author = (
            f"{ctx.author.name}({ctx.author.id})"
            if interaction is None else f"{interaction.user.name}({interaction.user.id})"
        )
        command = ctx.command if interaction is None else interaction.command.name
        if interaction is not None:
            await interaction.message.delete()
        if ctx is not None:
            await ctx.message.delete()
        incident_report_logger.info(f"{author} tried to run command {command}")
        send_fund = ctx.channel.send if ctx is not None else interaction.channel.send
        await send_fund(
            "You do not have adequate permission to run this command, incident will be reported"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        logger.error(f'[main.py on_command_error()] Missing argument: {error.param}')
        author = ctx.me.display_name if interaction is None else interaction.client.user.display_name
        avatar = ctx.me.display_avatar.url if interaction is None else interaction.client.user.display_avatar.url
        e_obj = await imported_embed(
            logger,
            interaction=interaction,
            ctx=ctx,
            author=author,
            avatar_url=avatar,
            description=f"Missing argument: {error.param}"
        )
        if e_obj is not False:
            if ctx is None:
                await interaction.response.send_message(embed=e_obj)
            else:
                await ctx.channel.send(embed=e_obj)
    elif isinstance(error, commands.errors.CommandNotFound):
        return
    else:
        # only prints out an error to the log if the string that was entered doesnt contain just "."
        pattern = r'[^\.]'
        if re.search(pattern, f"{error}"[9:-14]):
            if type(error) is discord.ext.commands.errors.CheckFailure:
                author = ctx.author if ctx is not None else f"{interaction.user.name}({interaction.user.id})"
                logger.warning(
                    f"[ManageTestGuild on_command_error()] user {author} "
                    "probably tried to access a command they arent supposed to"
                )
            else:
                try:
                    print_wall_e_exception(
                        error, error.__traceback__, error_logger=error.command.binding.logger.error
                    )
                except Exception:
                    print_wall_e_exception(error, error.__traceback__, error_logger=logger.error)
