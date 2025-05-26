import asyncio
import re

import discord
from discord.ext import commands

from utilities.embed import WallEColour, embed
from utilities.setup_logger import print_wall_e_exception


async def report_text_command_error(ctx, error):
    """
    Function that gets called when the script cant understand the command that the user invoked
    :param ctx: the ctx object that is part of command parameters that are not slash commands
    :param error: the error that was encountered
    :return:
    """
    from utilities.global_vars import logger
    handled_errors = (
        commands.errors.ArgumentParsingError, commands.errors.MemberNotFound, commands.MissingRequiredArgument,
        commands.errors.BadArgument, discord.errors.HTTPException
    )
    if isinstance(error, handled_errors):
        message_footer = (
            "\n\n**You have 20 seconds to copy your input to do a retry before I ensure it is wiped from the"
            " channel**"
        )
        if isinstance(error, commands.errors.ArgumentParsingError):
            description = (
                f"Uh-oh, seem like you have entered a badly formed string and wound up with error:"
                f"\n'{error.args[0]}'\n\n[Technical Details link if you care to look]"
                f"(https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?"
                f"highlight=argumentparsingerror#exceptions){message_footer}"
            )
        elif ctx.command.name == 'unban' and isinstance(error, commands.errors.BadArgument):
            description = f'Please enter a numerical Discord ID.{message_footer}'
        else:
            description = f"{error.args[0]}{message_footer}"
        error_type = f"{type(error)}"[8:-2]
        embed_obj = await embed(
            logger=ctx.cog.logger, ctx=ctx, title=f"Error {error_type} encountered",
            description=description, colour=WallEColour.ERROR
        )
        if embed_obj is not False:
            message = await ctx.channel.send(embed=embed_obj, reference=ctx.message)
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
        author = ctx.author if interaction is None else interaction.user
        bot = ctx.me if interaction is None else interaction.client.user
        command = ctx.command if interaction is None else interaction.command.name
        channel = ctx.channel if ctx is not None else interaction.channel

        if interaction is not None and interaction.message is not None:
            await interaction.message.delete()
        if ctx is not None:
            await ctx.message.delete()
        incident_report_logger.info(f"<@{author.id}> tried to run command `{command}`")
        e_obj = await embed(
            logger,
            interaction=interaction,
            ctx=ctx,
            title='INCIDENT REPORT',
            colour=WallEColour.ERROR,
            author=bot,
            description=(
                "You do not have adequate permission to run this command.\n\n"
                "Incident has been reported"
            )
        )
        if e_obj is not False:
            try:
                await author.send(embed=e_obj)
            except discord.errors.Forbidden:
                msg = await channel.send(f'<@{author.id}>', embed=e_obj)
                await asyncio.sleep(10)
                await msg.delete()
    elif isinstance(error, discord.app_commands.commands.CommandInvokeError):
        description = error.args[0]
        error_type = f"{type(error)}"[8:-2]
        embed_obj = await embed(
            logger=logger, interaction=interaction, title=f"Error {error_type} encountered",
            description=description, colour=WallEColour.ERROR
        )
        error.command.binding.logger.error(
            'Encountered exception in command %r', interaction.command.name, exc_info=error
        )
        errors = []
        msg = None
        if embed_obj is not False:
            deferred_interaction = interaction.response.type is not None
            if deferred_interaction:
                send_func = interaction.followup.send
            else:
                send_func = interaction.response.send_message
            try:
                await send_func(embed=embed_obj)
            except discord.errors.NotFound as e:
                if isinstance(e, discord.errors.NotFound):
                    errors.append(e)
                    try:
                        logger.error(
                            "[error_handlers.py report_command_errors()] experienced below error"
                            f" when trying to alert user of error '{description}' when using interaction "
                            f"response follow up attempt {type(e)}\n{e}"
                        )
                        # if responding to the interaction in any way failed, let's try and just send a
                        # general message to the channel
                        msg = await interaction.channel.send(embed=embed_obj)
                    except Exception as e:
                        errors.append(e)
                        logger.error(
                            "[error_handlers.py report_command_errors()] unable to send error embed"
                            f" to channel due to error {description} via any routes due to"
                            f" {type(e)}\n{errors}"
                        )
                else:
                    logger.error(
                        f"[error_handlers.py report_command_errors()] experienced unexpected error below when trying "
                        f"to send a response to the interaction due to error {description}: {type(e)}/\n{e}"
                    )
            await asyncio.sleep(20)
            await interaction.delete_original_response()
            if msg is not None:
                await msg.delete()
    elif isinstance(error, commands.errors.CommandNotFound):
        return
    elif isinstance(error, discord.errors.NotFound):
        try:
            error.command.binding.logger.warn(
                'Encountered exception in command %r', interaction.command.name, exc_info=error
            )
        except Exception:
            logger.warn(
                'Encountered exception in command %r', interaction.command.name, exc_info=error
            )
    else:
        # only prints out an error to the log if the string that was entered doesnt contain just "."
        pattern = r'[^\.]'
        if re.search(pattern, f"{error}"[9:-14]):
            if type(error) is discord.ext.commands.errors.CheckFailure:
                author = ctx.author if ctx is not None else f"{interaction.user.name}({interaction.user.id})"
                logger.warning(
                    f"[error_handlers.py on_command_error()] user {author} "
                    "probably tried to access a command they arent supposed to"
                )
            else:
                try:
                    print_wall_e_exception(
                        error, error.__traceback__, error_logger=error.command.binding.logger.error
                    )
                except Exception:
                    print_wall_e_exception(error, error.__traceback__, error_logger=logger.error)
