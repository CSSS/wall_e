# from discord.ext import commands
import discord
import asyncio # noqa, flake8 F401
import json # noqa, flake8 F401
import logging
logger = logging.getLogger('wall_e')


async def embed(ctx, title='', content='', description='', author='', colour=0x00bfbd, link='', thumbnail='',
                avatar='', footer=''):
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
    if len(title) > 256:
        title = str(title)
        length = str(len(title) - 256)
        await ctx.send(
            "Embed Error:\nlength of the title ```{}``` "
            "being added to the title field is {} characters "
            "too big, pleae cut down to a size of 256".format(
                title,
                length
            )
        )
        logger.info("[embed.py embed()] length of title [{}] being added to the field is too big".format(title))
        return False

    if len(description) > 2048:
        await ctx.send(
            "Embed Error:\nlength of description ```{}``` being added to the "
            "description field is {} characters too big, pleae cut "
            "down to a size of 2048".format(
                description[0:2000-135-len(str(len(description)-2048))],
                len(description) - 2048
            )
        )
        logger.info("[embed.py embed()] length of description [{}] being added to the "
                    "field is too big".format(description))
        return False

    if len(content) > 25:
        await ctx.send("Embed Error:\nlength of content ```{}``` being added to the content field "
                       "is {} characters too big, pleae cut down to a size of 25".format(content, len(content) - 25))
        logger.info("[embed.py embed()] length of content [{}] being added to the field is too big".format(content))
        return False

    for record in content:
        if len(record[0]) > 256:
            await ctx.send("Embed Error:\nlength of record ```{}``` being added to the name "
                           "field is {} characters too big, pleae cut down to a "
                           "size of 256".format(record[0], len(record[0] - 256)))
            logger.info("[embed.py embed()] length of record [{}] being added to the field "
                        "is too big".format(record[0]))
            return False
        if len(record[1]) > 1024:
            await ctx.send("Embed Error:\nlength of record ```{}``` being added to the value "
                           "field is {} characters too big, pleae cut down to a "
                           "size of 1024".format(record[1], len(record[1] - 1024)))
            logger.info("[embed.py embed()] length of record [{}] being added to the field "
                        "is too big".format(record[1]))
            return False

    if len(footer) > 2048:
        await ctx.send("Embed Error:\nlength of footer ```{0}``` being added to the footer field is {1}"
                       " characters too big, pleae cut down to a size of 2048".format(footer, len(footer) - 2048))
        logger.info("[embed.py embed()] length of footer [{}] being added to the field is too big".format(footer))
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
