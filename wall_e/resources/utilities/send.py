import aiohttp
import discord
import logging
logger = logging.getLogger('wall_e')


def getLastIndex(content, index, reservedSpace):
    # this when the the size of contents is too big for a single discord message, this means
    # that the message has to be split. and in order to make the output most visually appealing
    # when splitting it is to see if there is a newline on which  the message can be split instead.
    # if there is no suitable newline, it will instead just cut down an existing line
    logger.info("[send.py getLastIndex()] index =[" + str(index) + "] reservedSpace =[" + str(reservedSpace) + "]")
    if len(content) - index < 2000 - reservedSpace:
        logger.info("[send.py  getLastIndex()] returning length of content =[" + str(len(content)) + "]")
        return len(content)
    else:
        indexOfNewLine = content.rfind('\n', index, index + (2000 - reservedSpace))
        if indexOfNewLine != 0:
            lastIndex = indexOfNewLine
        else:
            lastIndex = 2000 - reservedSpace
        logger.info("[send.py getLastIndex()] indexOfNewLine =[" + str(indexOfNewLine) + "]")
        return lastIndex


async def send(ctx, content=None, tts=False, embed=None, file=None, files=None,
               delete_after=None, nonce=None, prefix=None, suffix=None):
    # adds the requested prefix and suffic to the contents
    formattedContent = content
    if prefix is not None:
        formattedContent = prefix + content
    if suffix is not None:
        formattedContent = formattedContent + suffix

    # so what basically happens is it first tries to send the full message, then if it cant, it breaks it
    # down into 2000 sizes messages and send them individually
    try:
        await ctx.send(formattedContent)
    except (aiohttp.ClientError, discord.errors.HTTPException):
        # used for determing how much space for each of the messages need to be reserved for the requested suffix
        # and prefix
        reservedSpace = 0
        if prefix is not None:
            reservedSpace += len(prefix)
        if suffix is not None:
            reservedSpace += len(suffix)
        logger.info("[send.py send()] reservedSpace = [" + str(reservedSpace) + "]")
        lastIndex = getLastIndex(content, 0, reservedSpace)
        first = True  # this is only necessary because it wouldnt make sense to have any potential embeds or file[s]
        # with each message
        firstIndex = 0
        finished = False
        while not finished:
            if first:
                first = False
                formattedContent = content[firstIndex:lastIndex]
                if prefix is not None:
                    formattedContent = prefix + formattedContent
                if suffix is not None:
                    formattedContent = formattedContent + suffix
                logger.info("[send.py send()] messaage sent off with firstIndex = ["
                            + str(firstIndex) + "] and lastIndex = [" + str(lastIndex) + "]")
                await ctx.send(formattedContent, tts=tts, embed=embed, file=file, files=files,
                               delete_after=delete_after, nonce=nonce)
            else:
                formattedContent = content[firstIndex:lastIndex]
                if prefix is not None:
                    formattedContent = prefix + formattedContent
                if suffix is not None:
                    formattedContent = formattedContent + suffix
                logger.info("[send.py send()] messaage sent off with firstIndex = [" + str(firstIndex)
                            + "] and lastIndex = [" + str(lastIndex) + "]")
                await ctx.send(formattedContent, tts=tts, delete_after=delete_after, nonce=nonce)
            firstIndex = lastIndex
            lastIndex = getLastIndex(content, firstIndex + 1, reservedSpace)
            logger.info("[send.py send()] lastIndex updated to " + str(lastIndex))
            if len(content[firstIndex:lastIndex]) == 0:
                finished = True
    except Exception as exc:
        exc_str = '{}: {}'.format(type(exc).__name__, exc)
        logger.error('[send.py send()] write to channel failed\n{}'.format(exc_str))
