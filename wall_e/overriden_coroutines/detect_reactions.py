import asyncio

import discord

from utilities.bot_channel_manager import wall_e_category_name
from utilities.embed import embed
from wall_e_models.customFields import pstdatetime


async def get_message_after_up_arrow_emoji(channel, message_with_up_arrow_emoji):
    messages = [message async for message in channel.history(limit=1, after=message_with_up_arrow_emoji)]
    return messages[0] if len(messages) > 0 else None


async def get_message_before_down_arrow_emoji(channel, reaction, message_after_message_with_up_arrow_emoji):
    message_before_message_with_down_arrow_emoji = message_after_message_with_up_arrow_emoji
    number_of_messages_crawled = 0
    upper_bound_traceback_message_index = -1
    while upper_bound_traceback_message_index == -1:
        messages = [message async for message in
                    channel.history(limit=100, before=message_before_message_with_down_arrow_emoji)]
        number_of_messages_crawled += 100
        iteration = 0
        if len(messages) > 0:
            while upper_bound_traceback_message_index == -1 and iteration < len(messages):
                upper_bound_emoji_detected = '⬇️' in [reaction.emoji for reaction in messages[iteration].reactions]
                if upper_bound_emoji_detected and reaction.message_id != messages[iteration].id:
                    upper_bound_traceback_message_index = iteration
                iteration += 1
        else:
            # could not find the original traceback message string
            # will just clear the whole channel instead I guess
            upper_bound_traceback_message_index = None

        if upper_bound_traceback_message_index == -1:
            # traceback message not found but there is more potential message to look through
            message_before_message_with_down_arrow_emoji = messages[len(messages) - 1]
        elif upper_bound_traceback_message_index is None:
            # whole channel has to be cleared
            message_before_message_with_down_arrow_emoji = None
        else:
            # message with down arrow found, will now try to find the message before it as that message is needed
            # for the "after" parameter when getting the whole block of messages to delete
            if len(messages) == upper_bound_traceback_message_index + 1:

                # seems the message before the traceback message was not retrieved in the messages list, so
                # another call needs to be made just for that message
                previous_messages = [
                    message async for message in
                    channel.history(limit=1, before=messages[upper_bound_traceback_message_index])
                ]
                # either a previous message exists and was obtained, indicating that there
                # is a suitable message for the "after" cursor or there is no previous
                # message, so "None" should be used
                message_before_message_with_down_arrow_emoji = previous_messages[0] if len(
                    previous_messages) > 0 else None
            else:
                # if the code was lucky, the message right before the Traceback is in the list of
                # messages that were already retrieved so the code just need to look at the next
                # message in the list for the "after" parameter
                message_before_message_with_down_arrow_emoji = messages[upper_bound_traceback_message_index + 1]
    return number_of_messages_crawled, message_before_message_with_down_arrow_emoji


async def reaction_detected(reaction):
    """
    Adding a listener method that allows the Bot_manager to delete a stack trace in an error text channel if
     a Bot_manager has fixed the error in the stack trace. Just a nice way to keep a clean error text channel and a
     quick visual indicator of whether an error has been fixed

    :param reaction:
    :return:
    """
    from utilities.global_vars import bot, logger
    guild = bot.guilds[0]
    delete_debug_log_reaction_detected = reaction.emoji.name == '⬆️'

    users_roles = [role.name for role in discord.utils.get(guild.members, id=reaction.user_id).roles]
    reaction_is_from_bot_manager = "Bot_manager" in users_roles

    channel_with_reaction = discord.utils.get(guild.channels, id=reaction.channel_id)
    reaction_not_sent_in_regular_channel = channel_with_reaction is None
    if reaction_not_sent_in_regular_channel:
        return
    channel_category = channel_with_reaction.category
    if channel_category is None:
        return
    text_channel_is_in_log_channel_category = channel_category.name == wall_e_category_name

    error_log_channel = channel_with_reaction.name[-6:] == '_error'
    warn_log_channel = channel_with_reaction.name[-5:] == '_warn'
    valid_error_channel = (
        delete_debug_log_reaction_detected and reaction_is_from_bot_manager and
        text_channel_is_in_log_channel_category and (error_log_channel or warn_log_channel)
    )
    if not valid_error_channel:
        return
    channel = channel_with_reaction
    message_with_up_arrow_emoji = await channel.fetch_message(reaction.message_id)

    message_after_message_with_up_arrow_emoji = await get_message_after_up_arrow_emoji(
        channel, message_with_up_arrow_emoji
    )
    (
        number_of_messages_crawled, message_before_message_with_down_arrow_emoji
    ) = await get_message_before_down_arrow_emoji(channel, reaction, message_after_message_with_up_arrow_emoji)

    messages_to_delete = [
        message async for message in channel.history(
            after=message_before_message_with_down_arrow_emoji, before=message_after_message_with_up_arrow_emoji,
            oldest_first=False, limit=number_of_messages_crawled
        )
    ]
    number_of_messages_deleted = len(messages_to_delete)
    todays_date = pstdatetime.now()
    messages_that_cant_be_bulk_deleted = []
    while len(messages_to_delete) > 0:
        number_of_messages = len(messages_to_delete)
        messages_that_can_be_deleted = [
            message_to_delete
            for message_to_delete in messages_to_delete[:100]
            if (todays_date - message_to_delete.created_at).days < 14
        ]
        messages_that_cant_be_bulk_deleted.extend([
            message_to_delete
            for message_to_delete in messages_to_delete[:100]
            if (todays_date - message_to_delete.created_at).days >= 14
        ])
        logger.info(
            f"[detect_reactions.py reaction_detected()] bulk deleting "
            f"{len(messages_that_can_be_deleted)}/{number_of_messages} messages "
        )
        await channel.delete_messages(messages_that_can_be_deleted, reason="issue fixed")
        messages_to_delete = messages_to_delete[100:]
    if len(messages_that_cant_be_bulk_deleted) > 0:
        logger.info(
            f"[detect_reactions.py reaction_detected()] attempting to manually delete "
            f"{len(messages_that_cant_be_bulk_deleted)} messages "
        )
        for message_that_cant_be_bulk_deleted in messages_that_cant_be_bulk_deleted:
            await message_that_cant_be_bulk_deleted.delete()
    message = (
        'Last' +
        (f" {number_of_messages_deleted} messages" if number_of_messages_deleted > 1 else " message") +
        " deleted"
    )
    e_obj = await embed(
        logger,
        ctx=channel,
        author=bot.user,
        description=message,
    )
    if e_obj is not False:
        message = await channel.send(embed=e_obj)
        await asyncio.sleep(10)
        await message.delete()
