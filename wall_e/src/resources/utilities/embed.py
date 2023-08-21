# from discord.ext import commands
import discord
import asyncio  # noqa, flake8 F401
import json  # noqa, flake8 F401
import logging

logger = logging.getLogger('wall_e')


async def embed(ctx_obj=None, send_message_func=None, title='', content='', description='', author='',
                colour=0x00bfbd, link='', thumbnail='', avatar='', footer=''):
    """
    title:<str> Title of the embed 99% of the time it'll be the command name, exceptions when it makes sense like
        with the sfu command.\n
    content:<array[tuples]> Array of tuples. Tuple per field of the embed. Field name at index 0 and value at index
        1. \n
    description:<str> Appears under the title. \n
    author:<str> Used to indicate user who involked the command or the bot itself when it makes sense like with the
        echo command.\n
    colour:<0x......> Used to set the coloured strip on the left side of the embed, by default set to a nice blue
        colour.\n
    link: <deprecated>\n
    thumbnail:<str> Url to image to be used in the embed. Thumbnail appears top right corner of the embed.\n
    avatar:<str> Used to set avatar next to author's name. Must be url. \n
    footer:<str> Used for whatever."""
    # these are put in place cause of the limits on embed described here
    # https://discordapp.com/developers/docs/resources/channel#embed-limits
    send = None
    if ctx_obj is not None:
        send = ctx_obj
    if send_message_func is not None:
        send = send_message_func
    if send is None:
        raise Exception("did not detect a ctx or interaction method")
    if len(title) > 256:
        title = f"{title}"
        await send(
            "Embed Error:\nlength of the title "
            f"being added to the title field is {len(title) - 256} characters "
            "too big, please cut down to a size of 256"
        )
        logger.info(f"[embed.py embed()] length of title [{title}] being added to the field is too big")
        return False

    if len(description) > 2048:
        await send(
            f"Embed Error:\nlength of description being added to the "
            f"description field is {len(description) - 2048} characters too big, please cut "
            "down to a size of 2048"
        )
        logger.info(f"[embed.py embed()] length of description [{description}] being added to the "
                    "field is too big")
        return False

    if len(content) > 25:
        await send(
            "Embed Error:\nlength of content being added to the content field "
            f"is {(len(content) - 25)} indices too big, please cut down to a size of 25"
        )
        logger.info("[embed.py embed()] length of content array will be added to the fields is too big")
        return False

    for idx, record in enumerate(content):
        if len(record[0]) > 256:
            await send(
                f"Embed Error:\nlength of record[0] for content index {idx} being added to the name "
                f"field is {(len(record[0]) - 256)} characters too big, please cut down to a size of 256"
            )
            logger.info("[embed.py embed()] length of following record being added to the field is too big")
            logger.info(f"[embed.py embed()] {record[0]}")
            return False
        if len(record[1]) > 1024:
            await send(
                f"Embed Error:\nlength of record[1] for content index {idx} being added to the value "
                f"field is {(len(record[1]) - 1024)} characters too big, please cut down to a "
                "size of 1024"
            )
            logger.info("[embed.py embed()] length of following record being added to the field is too big")
            logger.info(f"[embed.py embed()] {record[1]}")
            return False

    if len(footer) > 2048:
        await send(
            f"Embed Error:\nlength of footer being added to the footer field is "
            f"{len(footer) - 2048} characters too big, please cut down to a size of 2048"
        )
        logger.info(f"[embed.py embed()] length of footer [{footer}] being added to the field is too big")
        return False

    emb_obj = discord.Embed(title=title, type='rich')
    emb_obj.description = description
    emb_obj.set_author(name=author, icon_url=avatar)
    emb_obj.colour = colour
    emb_obj.set_thumbnail(url=thumbnail)
    emb_obj.set_footer(text=footer)
    # emb_obj.url = link
    # parse content to add fields
    for x in content:
        emb_obj.add_field(name=x[0], value=x[1], inline=False)
    return emb_obj
