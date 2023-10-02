import os
import time
from enum import Enum

import discord
import requests


class WallEColour(Enum):
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    FROSH_2020_THEME = 4


COLOUR_MAPPING = {
    WallEColour.INFO: 0x00bfbd,
    WallEColour.WARNING: 0xffc61d,
    WallEColour.ERROR: 0xA6192E,
    WallEColour.FROSH_2020_THEME: 0x00FF61
}


async def embed(logger, ctx=None, interaction=None, title='', content=None, description='', author='',
                colour: WallEColour = WallEColour.INFO, link='', thumbnail='', avatar_url='', footer=''):
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
    :param author: the author to assign to the name aprt of the embed's author [Optional]
     Used to indicate user who invoked the command or the bot itself when it makes sense like with the
     echo command.
    :param colour: <INFO|WARNING|ERROR> the message level to assign to the embed [Optional]
     Used to set the coloured strip on the left side of the embed, by default set to a nice blue colour.
    :param link: deprecated -  the link to assign to the embe
    :param thumbnail: the thumbnail to assign to the embed [Optional]
     Url to image to be used in the embed. Thumbnail appears top right corner of the embed.
    :param avatar_url: the avatar to assign to the icon_url part of embed's author [Optional]
     Used to set avatar next to author's name. Must be url.
    :param footer: the footer to assign to the embed [Optional]
    :return:
    """
    if content is None:
        content = []
    # these are put in place cause of the limits on embed described here
    # https://discordapp.com/developers/docs/resources/channel#embed-limits
    send_func = interaction.response.send_message if interaction is not None else ctx.send
    send_func = ctx.send if ctx is not None and send_func is None else send_func
    if send_func is None:
        raise Exception("did not detect a ctx or interaction method")
    if len(title) > 256:
        title = f"{title}"
        await send_func(
            "Embed Error:\nlength of the title "
            f"being added to the title field is {len(title) - 256} characters "
            "too big, please cut down to a size of 256"
        )
        logger.info(f"[embed.py embed()] length of title [{title}] being added to the field is too big")
        return False

    if len(description) > 2048:
        await send_func(
            f"Embed Error:\nlength of description being added to the "
            f"description field is {len(description) - 2048} characters too big, please cut "
            "down to a size of 2048"
        )
        logger.info(f"[embed.py embed()] length of description [{description}] being added to the "
                    "field is too big")
        return False

    if len(content) > 25:
        await send_func(
            "Embed Error:\nlength of content being added to the content field "
            f"is {(len(content) - 25)} indices too big, please cut down to a size of 25"
        )
        logger.info("[embed.py embed()] length of content array will be added to the fields is too big")
        return False

    for idx, record in enumerate(content):
        if len(record[0]) > 256:
            await send_func(
                f"Embed Error:\nlength of record[0] for content index {idx} being added to the name "
                f"field is {(len(record[0]) - 256)} characters too big, please cut down to a size of 256"
            )
            logger.info("[embed.py embed()] length of following record being added to the field is too big")
            logger.info(f"[embed.py embed()] {record[0]}")
            return False
        if len(record[1]) > 1024:
            await send_func(
                f"Embed Error:\nlength of record[1] for content index {idx} being added to the value "
                f"field is {(len(record[1]) - 1024)} characters too big, please cut down to a "
                "size of 1024"
            )
            logger.info("[embed.py embed()] length of following record being added to the field is too big")
            logger.info(f"[embed.py embed()] {record[1]}")
            return False

    if len(footer) > 2048:
        await send_func(
            f"Embed Error:\nlength of footer being added to the footer field is "
            f"{len(footer) - 2048} characters too big, please cut down to a size of 2048"
        )
        logger.info(f"[embed.py embed()] length of footer [{footer}] being added to the field is too big")
        return False

    emb_obj = discord.Embed(title=title, type='rich')
    emb_obj.description = description
    if avatar_url != "":
        from wall_e_models.models import EmbedAvatar
        # the below is needed in case the avatar url that was passed in to this function is deleted at some point
        # in the future, which will result in an embed that has a broken avatar
        avatar_obj = await EmbedAvatar.get_avatar_by_url(avatar_url)
        if avatar_obj is None:
            avatar_file_name = f'avatar-{time.time()*1000}.png'
            with open(avatar_file_name, "wb") as file:
                response = requests.get(avatar_url)
                file.write(response.content)
                channels = interaction.guild.channels if interaction is not None else ctx.guild.channels
                embed_avatar_chan: discord.TextChannel = discord.utils.get(channels, name="embed_avatars")
            avatar_msg = await embed_avatar_chan.send(file=discord.File(avatar_file_name))
            os.remove(avatar_file_name)
            avatar_obj = EmbedAvatar(
                avatar_discord_url=avatar_url,
                avatar_discord_permanent_url=avatar_msg.attachments[0].url
            )
            await EmbedAvatar.insert_record(avatar_obj)
        avatar_url = avatar_obj.avatar_discord_permanent_url
    emb_obj.set_author(name=author, icon_url=avatar_url)
    emb_obj.colour = COLOUR_MAPPING[colour]
    emb_obj.set_thumbnail(url=thumbnail)
    emb_obj.set_footer(text=footer)
    # emb_obj.url = link
    # parse content to add fields
    for x in content:
        emb_obj.add_field(name=x[0], value=x[1], inline=False)
    return emb_obj
