import aiohttp
import discord


def get_last_index(logger, content, index, reserved_space):
    """
    This when the the size of contents is too big for a single discord message, this means
     that the message has to be split. and in order to make the output most visually appealing
      when splitting it is to see if there is a newline on which  the message can be split instead.
       if there is no suitable newline, it will instead just cut down an existing line
    :param logger: the calling service's logger object
    :param content: the string that need to be cut down on
    :param index: the index to start of on when determining what is the max string that can be sent
    :param reserved_space: any prefixes that may need to be sent in all the messages that contain
     the split up string
    :return: the latest index that may need to be used in the next call to this function
    """

    logger.debug(f"[send.py get_last_index()] index =[{index}] reserved_space =[{reserved_space}]")
    if len(content) - index < 2000 - reserved_space:
        logger.debug(f"[send.py  get_last_index()] returning length of content =[{len(content)}]")
        return len(content)
    else:
        index_of_new_line = content.rfind('\n', index, index + (2000 - reserved_space))
        if index_of_new_line != 0:
            last_index = index_of_new_line
        else:
            last_index = 2000 - reserved_space
        logger.debug(f"[send.py get_last_index()] index_of_new_line =[{index_of_new_line}]")
        return last_index


async def send(logger, ctx, content=None, tts=False, embed=None, file=None, files=None,
               delete_after=None, nonce=None, prefix=None, suffix=None, reference=None):
    """
    send helper function that helps when dealing with a message that has too many characters
    :param logger: the calling service's logger object
    :param ctx: the ctx object that is in a command's parameter if it is a dot command
    :param content: the message that may need to be cut down
    :param tts: the tts flag to send to the discord send message
    :param embed: the embed that will need to be included in all the messages sent that contain
     the cut down content
    :param file: the file that will need to be included in all the messages sent that contain
     the cut down content
    :param files: the files that will need to be included in all the messages sent that contain
     the cut down content
    :param delete_after: how long to wait before deleting all the messages that were sent that contain
     the cut down content
    :param nonce: the nonce flag to send to the discord send message
    :param prefix: the prefix to surround all the messages that contain the cut down content
    :param suffix: the suffix to surround all the messages that contain the cut down content
    :param reference: the original message this message being sent is a reference to
    :return:
    """
    # adds the requested prefix and suffic to the contents
    formatted_content = content
    if prefix is not None:
        formatted_content = prefix + content
    if suffix is not None:
        formatted_content = formatted_content + suffix

    # so what basically happens is it first tries to send the full message, then if it cant, it breaks it
    # down into 2000 sizes messages and send them individually
    try:
        await ctx.send(formatted_content, reference=reference)
    except (aiohttp.ClientError, discord.errors.HTTPException):
        # used for determing how much space for each of the messages need to be reserved for the requested suffix
        # and prefix
        reserved_space = 0
        if prefix is not None:
            reserved_space += len(prefix)
        if suffix is not None:
            reserved_space += len(suffix)
        logger.debug(f"[send.py send()] reserved_space = [{reserved_space}]")
        last_index = get_last_index(logger, content, 0, reserved_space)
        first = True  # this is only necessary because it wouldnt make sense to have any potential embeds or file[s]
        # with each message
        first_index = 0
        finished = False
        while not finished:
            if first:
                first = False
                formatted_content = content[first_index:last_index]
                if prefix is not None:
                    formatted_content = prefix + formatted_content
                if suffix is not None:
                    formatted_content = formatted_content + suffix
                logger.debug(
                    f"[send.py send()] messaage sent off with first_index = [{first_index}] and last_index ="
                    f" [{last_index}]"
                )
                await ctx.send(formatted_content, tts=tts, embed=embed, file=file, files=files,
                               delete_after=delete_after, nonce=nonce, reference=reference)
            else:
                formatted_content = content[first_index:last_index]
                if prefix is not None:
                    formatted_content = prefix + formatted_content
                if suffix is not None:
                    formatted_content = formatted_content + suffix
                logger.debug(
                    f"[send.py send()] messaage sent off with first_index = [{first_index}] and last_index = "
                    f"[{last_index}]"
                )
                await ctx.send(
                    formatted_content, tts=tts, delete_after=delete_after, nonce=nonce, reference=reference
                )
            first_index = last_index
            last_index = get_last_index(logger, content, first_index + 1, reserved_space)
            logger.debug(f"[send.py send()] last_index updated to {last_index}")
            if len(content[first_index:last_index]) == 0:
                finished = True
    except Exception as exc:
        exc_str = f'{type(exc).__name__}: {exc}'
        logger.error(f'[send.py send()] write to channel failed\n{exc_str}')
