import discord
from discord.ext import tasks

from wall_e_models.models import HelpMessage
from utilities.setup_logger import print_wall_e_exception, log_exception


@tasks.loop(seconds=1)
async def delete_help_command_messages():
    from utilities.global_vars import bot, logger
    try:
        help_messages = await HelpMessage.get_messages_to_delete()
        for help_message in help_messages:
            channel = bot.get_channel(int(help_message.channel_id))
            if channel is not None:
                help_message_fetched = False
                help_message_already_deleted = False
                try:
                    message = await channel.fetch_message(int(help_message.message_id))
                    try:
                        invocator_message = await channel.fetch_message(int(message.reference.message_id))
                        await invocator_message.delete()
                    except discord.NotFound:
                        # means the original invocating message has since been deleted so the code can move on
                        pass
                    await message.delete()
                    help_message_fetched = True
                except discord.NotFound:
                    logger.info(
                        f"[delete_help_messages.py delete_help_command_messages()] could not find the "
                        f"message that contains the help command with obj {help_message}"
                    )
                    # seems the message is already deleted
                    help_message_already_deleted = True
                except discord.Forbidden:
                    log_exception(
                        logger,
                        "[delete_help_messages.py delete_help_command_messages()] "
                        f"wall_e does not seem to have permissions to view/delete the message that "
                        f"contains the help command with obj {help_message}"
                    )
                    # if wall_e does not have the permission to delete the message,
                    # a retry would not fix that anyways
                    help_message_fetched = True
                except discord.HTTPException:
                    log_exception(
                        logger,
                        "[delete_help_messages.py delete_help_command_messages()] "
                        f"some sort of HTTP prevented wall_e from deleting the message that "
                        f"contains the help command with obj {help_message}"
                    )
                    # there might be a momentary network glitch, best to try again
                if help_message_fetched or help_message_already_deleted:
                    await HelpMessage.delete_message(help_message)
    except Exception as error:
        print_wall_e_exception(error, error.__traceback__, error_logger=logger.error)
