import asyncio
from resources.utilities.embed import embed as imported_embed


async def paginate_embed(logger, bot, config, description_to_embed, title=" ", ctx=None, interaction=None):
    send_func = interaction.response.send_message if interaction is not None else None
    send_func = ctx.send if ctx is not None and send_func is None else send_func
    if send_func is None:
        raise Exception("did not detect a ctx or interaction method")
    num_of_pages = len(description_to_embed)
    logger.info(
        "[paginate.py paginate_embed()] called with following argument: "
        "title={}\n\ndescription_to_embed={}\n\n".format(title, description_to_embed)
    )

    current_page = 0
    first_run = True
    msg = None

    while True:
        logger.info("[paginate.py paginate_embed()] loading page {}".format(current_page))
        logger.info("[paginate.py paginate_embed()] loading roles {}".format(description_to_embed[current_page]))
        embed_obj = await imported_embed(
            logger,
            interaction=interaction,
            ctx=ctx,
            title=title,
            author=config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=description_to_embed[current_page],
            footer="{}/{}".format(current_page + 1, num_of_pages)
        )
        if embed_obj is not None:
            logger.info("[paginate.py paginate_embed()] embed succesfully created and populated for page "
                        + str(current_page))
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
            msg = await send_func(content=None, embed=embed_obj)
            if interaction is not None:
                msg = await interaction.original_response()
            logger.info("[paginate.py paginate_embed()] sent message")
        else:
            await msg.edit(embed=embed_obj)
            await msg.clear_reactions()
            logger.info("[paginate.py paginate_embed()] edited message")

        # adding reactions deemed necessary to page
        for reaction in to_react_unicode:
            await msg.add_reaction(reaction)

        logger.info("[paginate.py paginate_embed()] added all reactions to message")

        def check_reaction(reaction, user):
            if not user.bot:  # just making sure the bot doesnt take its own reactions
                # into consideration
                e = str(reaction.emoji)
                logger.info("[paginate.py paginate_embed()] reaction {} detected from {}".format(e, user))
                return e.startswith(('⏪', '⏩', '✅'))

        user_reacted = False
        while user_reacted is False:
            try:
                user_reacted = await bot.wait_for('reaction_add', timeout=20, check=check_reaction)
            except asyncio.TimeoutError:
                logger.info("[paginate.py paginate_embed()] timed out waiting for the user's reaction.")

            if user_reacted:
                if '⏪' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page - 1
                    if current_page < 0:
                        current_page = num_of_pages - 1
                    logger.info(
                        "[paginate.py paginate_embed()] user indicates they want to go back "
                        "a page from {} to {}".format(prev_page, current_page)
                    )

                elif '⏩' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page + 1
                    if current_page == num_of_pages:
                        current_page = 0
                    logger.info(
                        "[paginate.py paginate_embed()] user indicates they want to go forward "
                        "a page from {} to {}".format(prev_page, current_page)
                    )

                elif '✅' == user_reacted[0].emoji:
                    logger.info(
                        "[paginate.py paginate_embed()] user indicates they are done with the "
                        "roles command, deleting roles message"
                    )
                    await msg.delete()
                    return
            else:
                logger.info("[paginate.py paginate_embed()] deleting message")
                await msg.delete()
                return


async def paginate(logger, bot, ctx, list_to_paginate, num_of_pages=0, num_of_page_entries=0, title=" "):
    logger.info(
        "[paginate.py paginate()] called with following argument: list_to_paginate={}"
        "\n\tnum_of_pages={}, num_of_page_entries={} and title={}".format(
            list_to_paginate,
            num_of_pages,
            num_of_page_entries,
            title
        )
    )
    if num_of_pages == 0:
        if num_of_page_entries == 0:
            logger.info(
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
            logger.info(
                "[paginate.py paginate()] you specified both "
                "\"num_of_pages\" and \"num_of_page_entries\", please only use one"
            )
        else:
            if int(len(list_to_paginate) / num_of_pages) == len(list_to_paginate) / num_of_pages:
                num_of_page_entries = int(len(list_to_paginate) / num_of_pages)
            else:
                num_of_page_entries = int(len(list_to_paginate) / num_of_pages) + 1

    logger.info(
        "[paginate.py paginate()] num_of_page_entries set to {} and "
        "num_of_pages set to {}".format(num_of_page_entries, num_of_pages)
    )
    list_of_roles = [["" for x in range(num_of_page_entries)] for y in range(num_of_pages)]
    x, y = 0, 0
    for roles in list_to_paginate:
        list_of_roles[y][x] = roles
        x += 1
        if x == num_of_page_entries:
            y += 1
            x = 0
    logger.info("[paginate.py paginate()] list added to roles matrix for pagination")
    current_page = 0
    first_run = True
    msg = None
    while True:
        logger.info("[paginate.py paginate()] loading page {}".format(current_page))
        logger.info("[paginate.py paginate()] loading roles {}".format(list_of_roles[current_page]))
        output = "{}\n\n```".format(title)
        for x in list_of_roles[current_page]:
            if x != '':
                output += '\t\"{}\"\n'.format(x)
        output += '```{}/{}'.format(str(current_page + 1), str(num_of_pages))
        logger.info("[paginate.py paginate()] created and filled Embed with roles of the current page "
                    + str(current_page))

        # determining which reactions are needed
        if num_of_pages == 1:
            to_react_unicode = [u"\U00002705"]
        else:
            to_react_unicode = [u"\U000023EA", u"\U000023E9", u"\U00002705"]

        if first_run:
            first_run = False
            msg = await ctx.send(output)
            logger.info("[paginate.py paginate()] sent message")
        else:
            await msg.edit(content=output)
            await msg.clear_reactions()
            logger.info("[paginate.py paginate()] edited message")

        for reaction in to_react_unicode:
            await msg.add_reaction(reaction)

        logger.info("[paginate.py paginate()] added all reactions to message")

        def check_reaction(reaction, user):
            if not user.bot:
                e = str(reaction.emoji)
                logger.info("[paginate.py paginate()] reaction {} detected from {}".format(e, user))
                return e.startswith(('⏪', '⏩', '✅'))

        user_reacted = False
        while user_reacted is False:
            try:
                user_reacted = await bot.wait_for('reaction_add', timeout=20, check=check_reaction)
            except asyncio.TimeoutError:
                logger.info("[paginate.py paginate()] timed out waiting for the user's reaction.")

            if user_reacted:
                if '⏪' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page - 1
                    if current_page < 0:
                        current_page = num_of_pages - 1
                    logger.info(
                        "[paginate.py paginate()] user indicates "
                        "they want to go back a page from {} to {}".format(prev_page, current_page)
                    )
                elif '⏩' == user_reacted[0].emoji:
                    prev_page = current_page
                    current_page = current_page + 1
                    if current_page == num_of_pages:
                        current_page = 0
                    logger.info(
                        "[paginate.py paginate()] user indicates they want"
                        " to go forward a page from {} to {}".format(prev_page, current_page)
                    )
                elif '✅' == user_reacted[0].emoji:
                    logger.info(
                        "[paginate.py paginate()] user indicates they are done "
                        "with the roles command, deleting roles message"
                    )
                    await msg.delete()
                    return
            else:
                logger.info("[paginate.py paginate()] deleting message")
                await msg.delete()
                return
