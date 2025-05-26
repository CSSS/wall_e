import os
import time
from enum import Enum

import discord
import requests
from discord.ext import commands

from utilities.global_vars import wall_e_config


class WallEColour(Enum):
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    FROSH_2020_THEME = 4
    BAN = 5


COLOUR_MAPPING = {
    WallEColour.INFO: 0x00bfbd,
    WallEColour.WARNING: 0xffc61d,
    WallEColour.ERROR: 0xA6192E,
    WallEColour.FROSH_2020_THEME: 0x00FF61,
    WallEColour.BAN: discord.Color.red()
}


async def send_func_helper(message, send_func, text_command, reference):
    if text_command:
        await send_func(message, reference=reference)
    else:
        await send_func(message)


async def embed(logger, ctx: commands.context = None, interaction: discord.Interaction = None, title: str = '',
                content: list = None, description: str = '', author: discord.Member = None, author_name: str = '',
                author_icon_url: str = '', colour: WallEColour = WallEColour.INFO, thumbnail: str = '',
                footer_text: str = '', footer_icon=None, timestamp=None, channels=None, ban_related_message=False,
                bot_management_channel=None):
    """
    Embed creation helper function that validates the input to ensure it does not exceed the discord limits
    :param logger: the logger instance from the service
    :param ctx: the ctx object that is in the command's arguments if it was a dot command [need to be specified if
     no interaction is detected]
    :param interaction: the interaction object that is in the command's arguments if it was a slash command [need to
     be specified if no ctx is detected]
    :param title: the title to assign to the embed [Optional]
     99% of the time it'll be the command name, exceptions when it makes sense like
     with the sfu command.
    :param content: array of tuples that are the content for the embed that is set to the add_field
     part of the embed [Optional]
     Tuple per field of the embed. Field name at index 0 and value at index 1.
    :param description: the description to assign to the embed [Optional]
     Appears under the title.
    :param author: the discord Member whose name and avatar has to be used as part of the
     author section of the embed [Optional].
     Examples of how to access the Member object with text command
      - author = ctx.author # individual who invoked command
      - author = ctx.me # bot will be used as author

     Examples of how to access the Member object with slash command
      - author = interaction.user # individual who invoked command
      - author = interaction.client.user # bot will be used as author
    :param author_name: the name to assign to the name part of the embed's author [Optional]
     Used to indicate user who invoked the command or the bot itself when it makes sense like with the
     echo command.
    :param author_icon_url: the avatar to assign to the icon_url part of embed's author [Optional]
     Used to set avatar next to author's name. Must be url.
    :param colour: <INFO|WARNING|ERROR> the message level to assign to the embed [Optional]
     Used to set the coloured strip on the left side of the embed, by default set to a nice blue colour.
    :param thumbnail: the thumbnail to assign to the embed [Optional]
     Url to image to be used in the embed. Thumbnail appears top right corner of the embed.
    :param footer_text: the footer text to assign to the embed [Optional]
    :param footer_icon: the icon to assign to the footer [Optional]
    :param timestamp: the timestamp to assign to the footer [Optional]
    :param channels: the channels in the guild, necessary for the embed that are created from the intercept and
     watchdog methods in ban class
    :param ban_related_message: indicates if the embed function was called from the ban_related messages which have no
     context or interaction object
    :param bot_management_channel: provides a way for the non-context and non-interaction classes in the ban class
     to send their error messages somewhere
    :return:
    """
    if content is None:
        content = []
    # these are put in place cause of the limits on embed described here
    # https://discord.com/developers/docs/resources/message#embed-object-embed-limits

    if ctx is not None:
        # added below ternary because of detect_reaction calls this function without context, but rather passes in
        # a channel object
        reference = ctx.message if hasattr(ctx, "message") else None
        text_command = True
        send_func = ctx.send
    elif interaction is not None:
        reference = None
        text_command = False
        deferred_interaction = interaction.response.type is not None
        if deferred_interaction:
            send_func = interaction.followup.send
        else:
            send_func = interaction.response.send_message
    elif ban_related_message:
        reference = False
        text_command = False
        send_func = bot_management_channel.send
    else:
        raise Exception("did not detect a ctx or interaction method")
    if channels is None and ctx is None and interaction is None:
        raise Exception("Unable to get the channels on this guild")

    if len(title) > 256:
        title = f"{title}"
        await send_func_helper(
            "Embed Error:\nlength of the title "
            f"being added to the title field is {len(title) - 256} characters "
            "too big, please cut down to a size of 256",
            send_func, text_command, reference
        )
        logger.debug(f"[embed.py embed()] length of title [{title}] being added to the field is too big")
        return False
    if description is None and content is None:
        await send_func_helper(
            "Embed Error:\nThere need to be either a description or fields specified",
            send_func, text_command, reference
        )
        logger.debug("[embed.py embed()] There need to be either a description or fields specified")
        return False
    if description is not None and len(description) > 2048:
        await send_func_helper(
            f"Embed Error:\nlength of description being added to the "
            f"description field is {len(description) - 2048} characters too big, please cut "
            "down to a size of 2048",
            send_func, text_command, reference
        )
        logger.debug(f"[embed.py embed()] length of description [{description}] being added to the "
                     "field is too big")
        return False

    if content is not None and len(content) > 25:
        await send_func_helper(
            "Embed Error:\nlength of content being added to the content field "
            f"is {(len(content) - 25)} indices too big, please cut down to a size of 25",
            send_func, text_command, reference
        )
        logger.debug("[embed.py embed()] length of content array will be added to the fields is too big")
        return False
    if content is not None:
        for idx, record in enumerate(content):
            if len(record[0]) > 256:
                await send_func_helper(
                    f"Embed Error:\nlength of record[0] for content index {idx} being added to the name "
                    f"field is {(len(record[0]) - 256)} characters too big, please cut down to a size of 256",
                    send_func, text_command, reference
                )
                logger.debug("[embed.py embed()] length of following record being added to the field is too big")
                logger.debug(f"[embed.py embed()] {record[0]}")
                return False
            if len(record[1]) > 1024:
                await send_func_helper(
                    f"Embed Error:\nlength of record[1] for content index {idx} being added to the value "
                    f"field is {(len(record[1]) - 1024)} characters too big, please cut down to a "
                    "size of 1024", send_func, text_command, reference
                )
                logger.debug("[embed.py embed()] length of following record being added to the field is too big")
                logger.debug(f"[embed.py embed()] {record[1]}")
                return False

    if len(footer_text) > 2048:
        await send_func_helper(
            f"Embed Error:\nlength of footer being added to the footer field is "
            f"{len(footer_text) - 2048} characters too big, please cut down to a size of 2048", send_func,
            text_command, reference
        )
        logger.debug(f"[embed.py embed()] length of footer [{footer_text}] being added to the field is too big")
        return False

    emb_obj = discord.Embed(title=title, type='rich')
    if description is not None:
        emb_obj.description = description
    if author is not None:
        author_name = author.display_name
        author_icon_url = author.display_avatar.url
    if author_icon_url != "":
        if channels is None:
            channels = interaction.guild.channels if interaction is not None else ctx.guild.channels
        embed_avatar_chan_name = wall_e_config.get_config_value('channel_names', 'EMBED_AVATAR_CHANNEL')
        embed_avatar_chan: discord.TextChannel = discord.utils.get(channels, name=embed_avatar_chan_name)
        from wall_e_models.models import EmbedAvatar
        # the below is needed in case the avatar url that was passed in to this function is deleted at some point
        # in the future, which will result in an embed that has a broken avatar
        avatar_obj = await EmbedAvatar.get_avatar_by_url(author_icon_url)
        if avatar_obj is None:
            avatar_file_name = f'avatar-{time.time()*1000}.png'
            with open(avatar_file_name, "wb") as file:
                file.write(requests.get(author_icon_url).content)
            avatar_msg = await embed_avatar_chan.send(file=discord.File(avatar_file_name))
            os.remove(avatar_file_name)
            avatar_obj = EmbedAvatar(
                avatar_discord_url=author_icon_url,
                avatar_discord_permanent_url=avatar_msg.attachments[0].url
            )
            await EmbedAvatar.insert_record(avatar_obj)
        author_icon_url = avatar_obj.avatar_discord_permanent_url
    emb_obj.set_author(name=author_name, icon_url=author_icon_url)
    emb_obj.colour = COLOUR_MAPPING[colour]
    emb_obj.set_thumbnail(url=thumbnail)
    if footer_text or footer_icon:
        if footer_icon is None:
            emb_obj.set_footer(text=footer_text)
        elif footer_text is None:
            emb_obj.set_footer(icon_url=footer_icon)
        else:
            emb_obj.set_footer(text=footer_text, icon_url=footer_icon)
    if timestamp:
        emb_obj.timestamp = timestamp
    # emb_obj.url = link
    # parse content to add fields
    if content is not None:
        for x in content:
            inline = x[2] if len(x) > 2 else True
            emb_obj.add_field(name=x[0], value=x[1], inline=inline)
    return emb_obj
