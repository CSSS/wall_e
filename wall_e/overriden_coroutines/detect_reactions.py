import asyncio
import discord


from utilities.bot_channel_manager import wall_e_category_name
from utilities.embed import embed


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
    stack_trace_has_been_tackled = reaction.emoji.name == '👍🏿'

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
    valid_error_channel = (
        stack_trace_has_been_tackled and reaction_is_from_bot_manager and
        text_channel_is_in_log_channel_category and error_log_channel
    )
    if not valid_error_channel:
        return
    traceback_message_index = -1
    channel = channel_with_reaction
    last_message_checked = None

    # will try to find the message that contains the Traceback string as that's the most reliable way to
    # detect the beginning of a stack trace in a channel
    while traceback_message_index == -1:
        messages = [message async for message in channel.history(limit=100, before=last_message_checked)]
        iteration = 0
        if len(messages) > 0:
            while traceback_message_index == -1 and iteration < len(messages):
                if "Traceback (most recent call last):" in messages[iteration].content:
                    traceback_message_index = iteration
                iteration += 1
        else:
            # could not find the original traceback message string
            # will just clear the whole channel instead I guess
            traceback_message_index = None

        if traceback_message_index == -1:
            # traceback message not found but there is more potential message to look through
            last_message_checked = messages[len(messages) - 1]
        elif traceback_message_index is None:
            # whole channel has to be cleared
            last_message_checked = None
        else:
            # traceback message found, will now try to find the message before it as that message is needed
            # for the "after" parameter when getting the whole stacktrace
            if len(messages) == traceback_message_index + 1:

                # seems the message before the traceback message was not retrieved in the messages list, so
                # another call needs to be made just for that message
                previous_messages = [
                    message async for message in
                    channel.history(limit=1, before=messages[traceback_message_index])
                ]
                # either a previous message exists and was obtained, indicating that there
                # is a suitable message for the "after" cursor or there is no previous
                # message, so "None" should be used
                last_message_checked = previous_messages[0] if len(previous_messages) > 0 else None
            else:
                # if the code was lucky, the message right before the Traceback is in the list of
                # messages that were already retrieved so the code just need to look at the next
                # message in the list for the "after" parameter
                last_message_checked = messages[traceback_message_index + 1]
    messages_to_delete = [
        message async for message in channel.history(after=last_message_checked, oldest_first=False)
    ]
    await channel.delete_messages(messages_to_delete, reason="issue fixed")
    message = (
        'Last' +
        (f" {len(messages_to_delete)} messages" if len(messages_to_delete) > 1 else " message") +
        " deleted"
    )
    e_obj = await embed(
        logger,
        ctx=channel,
        author=bot.user.display_name,
        avatar=bot.user.display_avatar.url,
        description=message,
    )
    if e_obj is not False:
        message = await channel.send(embed=e_obj)
        await asyncio.sleep(10)
        await message.delete()
