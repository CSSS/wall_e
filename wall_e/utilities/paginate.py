import asyncio

from utilities.embed import embed as imported_embed
from utilities.setup_logger import log_exception


async def send_func_helper(embed_obj, send_func, text_command, reference):
    if text_command:
        return await send_func(embed=embed_obj, reference=reference)
    else:
        return await send_func(embed=embed_obj)


async def paginate_embed(logger, bot, description_to_embed=None, content_to_embed=None, title=" ", ctx=None,
                         interaction=None):
    """
    Creates an interactive paginated embed message
    :param logger: the calling serivce's logger object
    :param bot: the bot which is needed to detect emoji reactions
    :param description_to_embed: a list of string descriptions that will be used in the embed
    :param content_to_embed:
    :param title: the title of the embed [Optional]
    :param ctx: the ctx object that is in the command's arguments if it was a dot command
     [need to be specified if no interaction is detected]
    :param interaction: the interaction object that is in the command's arguments if it was a slash command
     [need to be specified if no ctx is detected]
    :return:
    """
    if ctx is not None:
        reference = ctx.message
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
    else:
        log_exception(logger, "did not detect a ctx or interaction method")
    num_of_pages = len(description_to_embed) if description_to_embed is not None else len(content_to_embed)
    logger.debug(
        "[paginate.py paginate_embed()] called with following argument: "
        f"title={title}\n\ndescription_to_embed={description_to_embed}\n\ncontent_to_embed={content_to_embed}"
    )
    embed_author = ctx.me if interaction is None else interaction.client.user

    current_page = 0
    first_run = True
    msg = None

    while True:
        logger.debug(f"[paginate.py paginate_embed()] loading page {current_page}")
        if description_to_embed is not None:
            logger.debug(f"[paginate.py paginate_embed()] loading roles {description_to_embed[current_page]}")
        if content_to_embed is not None:
            logger.debug(f"[paginate.py paginate_embed()] loading roles {content_to_embed[current_page]}")
        embed_obj = await imported_embed(
            logger,
            interaction=interaction,
            ctx=ctx,
            title=title,
            author=embed_author,
            description=description_to_embed if description_to_embed is None else description_to_embed[current_page],
            content=content_to_embed if content_to_embed is None else content_to_embed[current_page],
            footer_text=f"{current_page + 1}/{num_of_pages}"
        )
        if embed_obj is not None:
            logger.debug(
                f"[paginate.py paginate_embed()] embed succesfully created and populated for page {current_page}"
            )
        else:
            return

        # determining which reactions are needed
        if num_of_pages == 1:
            to_react_unicode = [u"\U00002705"]
        else:
            to_react_unicode = [u"\U000023EA", u"\U000023E9", u"\U00002705"]

        # setting the content if it was the first run through or not.
        if first_run is True:
            first_run = False
            msg = await send_func_helper(embed_obj, send_func, text_command, reference)
            if interaction is not None:
                msg = await interaction.original_response()
            logger.debug("[paginate.py paginate_embed()] sent message")
        else:
            await msg.edit(embed=embed_obj)
            await msg.clear_reactions()
            logger.debug("[paginate.py paginate_embed()] edited message")

        # adding reactions deemed necessary to page
        for reaction in to_react_unicode:
            await msg.add_reaction(reaction)

        logger.debug("[paginate.py paginate_embed()] added all reactions to message")

        def check_reaction(reaction, user):
            if not user.bot:  # just making sure the bot doesnt take its own reactions
                # into consideration
                e = str(reaction.emoji)
                logger.debug(f"[paginate.py paginate_embed()] reaction {e} detected from {user}")
                return e.startswith(('⏪', '⏩', '✅'))

        user_reacted = False
        while user_reacted is False:
            try:
                user_reacted = await bot.wait_for('reaction_add', timeout=20, check=check_reaction)
            except asyncio.TimeoutError:
                logger.debug("[paginate.py paginate_embed()] timed out waiting for the user's reaction.")

            if user_reacted:
                if '⏪' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page - 1
                    if current_page < 0:
                        current_page = num_of_pages - 1
                    logger.debug(
                        "[paginate.py paginate_embed()] user indicates they want to go back "
                        f"a page from {prev_page} to {current_page}"
                    )

                elif '⏩' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page + 1
                    if current_page == num_of_pages:
                        current_page = 0
                    logger.debug(
                        "[paginate.py paginate_embed()] user indicates they want to go forward "
                        f"a page from {prev_page} to {current_page}"
                    )

                elif '✅' == user_reacted[0].emoji:
                    logger.debug(
                        "[paginate.py paginate_embed()] user indicates they are done with the "
                        "roles command, deleting roles message"
                    )
                    await msg.delete()
                    return
            else:
                logger.debug("[paginate.py paginate_embed()] deleting message")
                await msg.delete()
                return


async def paginate(logger, bot, ctx, list_to_paginate, num_of_pages=0, num_of_page_entries=0, title=" "):
    """
    Apparently not being used anywhere to not gonna bother adding function header comments
    :param logger:
    :param bot:
    :param ctx:
    :param list_to_paginate:
    :param num_of_pages:
    :param num_of_page_entries:
    :param title:
    :return:
    """
    logger.debug(
        f"[paginate.py paginate()] called with following argument: list_to_paginate={list_to_paginate}"
        f"\n\tnum_of_pages={num_of_pages}, num_of_page_entries={num_of_page_entries} and title={title}"
    )
    if num_of_pages == 0:
        if num_of_page_entries == 0:
            logger.debug(
                "[paginate.py paginate()] you need to specify either \"num_of_pages\" or \"num_of_page_entries\""
            )
            return
        else:
            if int(len(list_to_paginate) / num_of_page_entries) == len(list_to_paginate) / num_of_page_entries:
                num_of_pages = int(len(list_to_paginate) / num_of_page_entries)
            else:
                num_of_pages = int(len(list_to_paginate) / num_of_page_entries) + 1
    else:
        if num_of_page_entries != 0:
            logger.debug(
                "[paginate.py paginate()] you specified both "
                "\"num_of_pages\" and \"num_of_page_entries\", please only use one"
            )
        else:
            if int(len(list_to_paginate) / num_of_pages) == len(list_to_paginate) / num_of_pages:
                num_of_page_entries = int(len(list_to_paginate) / num_of_pages)
            else:
                num_of_page_entries = int(len(list_to_paginate) / num_of_pages) + 1

    logger.debug(
        f"[paginate.py paginate()] num_of_page_entries set to {num_of_page_entries} and "
        f"num_of_pages set to {num_of_pages}"
    )
    list_of_roles = [["" for x in range(num_of_page_entries)] for y in range(num_of_pages)]
    x, y = 0, 0
    for roles in list_to_paginate:
        list_of_roles[y][x] = roles
        x += 1
        if x == num_of_page_entries:
            y += 1
            x = 0
    logger.debug("[paginate.py paginate()] list added to roles matrix for pagination")
    current_page = 0
    first_run = True
    msg = None
    while True:
        logger.debug(f"[paginate.py paginate()] loading page {current_page}")
        logger.debug(f"[paginate.py paginate()] loading roles {list_of_roles[current_page]}")
        output = f"{title}\n\n```"
        for x in list_of_roles[current_page]:
            if x != '':
                output += f'\t\"{x}\"\n'
        output += f'```{current_page + 1}/{num_of_pages}'
        logger.debug(
            f"[paginate.py paginate()] created and filled Embed with roles of the current page {current_page}"
        )

        # determining which reactions are needed
        if num_of_pages == 1:
            to_react_unicode = [u"\U00002705"]
        else:
            to_react_unicode = [u"\U000023EA", u"\U000023E9", u"\U00002705"]

        if first_run:
            first_run = False
            msg = await ctx.send(output)
            logger.debug("[paginate.py paginate()] sent message")
        else:
            await msg.edit(content=output)
            await msg.clear_reactions()
            logger.debug("[paginate.py paginate()] edited message")

        for reaction in to_react_unicode:
            await msg.add_reaction(reaction)

        logger.debug("[paginate.py paginate()] added all reactions to message")

        def check_reaction(reaction, user):
            if not user.bot:
                e = str(reaction.emoji)
                logger.debug(f"[paginate.py paginate()] reaction {e} detected from {user}")
                return e.startswith(('⏪', '⏩', '✅'))

        user_reacted = False
        while user_reacted is False:
            try:
                user_reacted = await bot.wait_for('reaction_add', timeout=20, check=check_reaction)
            except asyncio.TimeoutError:
                logger.debug("[paginate.py paginate()] timed out waiting for the user's reaction.")

            if user_reacted:
                if '⏪' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page - 1
                    if current_page < 0:
                        current_page = num_of_pages - 1
                    logger.debug(
                        "[paginate.py paginate()] user indicates "
                        f"they want to go back a page from {prev_page} to {current_page}"
                    )
                elif '⏩' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page + 1
                    if current_page == num_of_pages:
                        current_page = 0
                    logger.debug(
                        "[paginate.py paginate()] user indicates they want"
                        f" to go forward a page from {prev_page} to {current_page}"
                    )
                elif '✅' == user_reacted[0].emoji:
                    logger.debug(
                        "[paginate.py paginate()] user indicates they are done "
                        "with the roles command, deleting roles message"
                    )
                    await msg.delete()
                    return
            else:
                logger.debug("[paginate.py paginate()] deleting message")
                await msg.delete()
                return
