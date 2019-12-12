# from discord.ext import commands
# import discord
import asyncio
import logging
from resources.utilities.embed import embed as imported_embed

logger = logging.getLogger('wall_e')


async def paginateEmbed(bot, ctx, config, descriptionToEmbed, title=" "):
    numOfPages = len(descriptionToEmbed)
    logger.info(
        "[paginate.py paginateEmbed()] called with following argument: "
        "title={}\n\ndescriptionToEmbed={}\n\n".format(title, descriptionToEmbed)
    )

    currentPage = 0
    firstRun = True
    msg = None

    while True:
        logger.info("[paginate.py paginateEmbed()] loading page {}".format(currentPage))
        logger.info("[paginate.py paginateEmbed()] loading roles {}".format(descriptionToEmbed[currentPage]))
        embedObj = await imported_embed(
            ctx,
            title=title,
            author=config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=config.get_config_value('bot_profile', 'BOT_AVATAR'),
            description=descriptionToEmbed[currentPage],
            footer="{}/{}".format(currentPage + 1, numOfPages)
        )
        if embedObj is not None:
            logger.info("[paginate.py paginateEmbed()] embed succesfully created and populated for page "
                        + str(currentPage))
        else:
            return

        # determining which reactions are needed
        if numOfPages == 1:
            toReactUnicode = [u"\U00002705"]
        else:
            toReactUnicode = [u"\U000023EA", u"\U000023E9", u"\U00002705"]

        # setting the content if it was the first run through or not.
        if firstRun is True:
            firstRun = False
            msg = await ctx.send(content=None, embed=embedObj)
            logger.info("[paginate.py paginateEmbed()] sent message")
        else:
            await msg.edit(embed=embedObj)
            await msg.clear_reactions()
            logger.info("[paginate.py paginateEmbed()] edited message")

        # adding reactions deemed necessary to page
        for reaction in toReactUnicode:
            await msg.add_reaction(reaction)

        logger.info("[paginate.py paginateEmbed()] added all reactions to message")

        def checkReaction(reaction, user):
            if not user.bot:  # just making sure the bot doesnt take its own reactions
                # into consideration
                e = str(reaction.emoji)
                logger.info("[paginate.py paginateEmbed()] reaction {} detected from {}".format(e, user))
                return e.startswith(('⏪', '⏩', '✅'))

        userReacted = False
        while userReacted is False:
            try:
                userReacted = await bot.wait_for('reaction_add', timeout=20, check=checkReaction)
            except asyncio.TimeoutError:
                logger.info("[paginate.py paginateEmbed()] timed out waiting for the user's reaction.")

            if userReacted:
                if '⏪' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage - 1
                    if currentPage < 0:
                        currentPage = numOfPages - 1
                    logger.info(
                        "[paginate.py paginateEmbed()] user indicates they want to go back "
                        "a page from {} to {}".format(prevPage, currentPage)
                    )

                elif '⏩' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage + 1
                    if currentPage == numOfPages:
                        currentPage = 0
                    logger.info(
                        "[paginate.py paginateEmbed()] user indicates they want to go forward "
                        "a page from {} to {}".format(prevPage, currentPage)
                    )

                elif '✅' == userReacted[0].emoji:
                    logger.info(
                        "[paginate.py paginateEmbed()] user indicates they are done with the "
                        "roles command, deleting roles message"
                    )
                    await msg.delete()
                    return
            else:
                logger.info("[paginate.py paginateEmbed()] deleting message")
                await msg.delete()
                return


async def paginate(bot, ctx, listToPaginate, numOfPages=0, numOfPageEntries=0, title=" "):
    logger.info(
        "[paginate.py paginate()] called with following argument: listToPaginate={}"
        "\n\tnumOfPages={}, numOfPageEntries={} and title={}".format(
            listToPaginate,
            numOfPages,
            numOfPageEntries,
            title
        )
    )
    if numOfPages == 0:
        if numOfPageEntries == 0:
            logger.info(
                "[paginate.py paginate()] you need to specify either \"numOfPages\" or \"numOfPageEntries\""
            )
            return
        else:
            if int(len(listToPaginate) / numOfPageEntries) == len(listToPaginate) / numOfPageEntries:
                numOfPages = int(len(listToPaginate) / numOfPageEntries)
            else:
                numOfPages = int(len(listToPaginate) / numOfPageEntries) + 1
    else:
        if numOfPageEntries != 0:
            logger.info(
                "[paginate.py paginate()] you specified both "
                "\"numOfPages\" and \"numOfPageEntries\", please only use one"
            )
        else:
            if int(len(listToPaginate) / numOfPages) == len(listToPaginate) / numOfPages:
                numOfPageEntries = int(len(listToPaginate) / numOfPages)
            else:
                numOfPageEntries = int(len(listToPaginate) / numOfPages) + 1

    logger.info(
        "[paginate.py paginate()] numOfPageEntries set to {} and "
        "numOfPages set to {}".format(numOfPageEntries, numOfPages)
    )
    listOfRoles = [["" for x in range(numOfPageEntries)] for y in range(numOfPages)]
    x, y = 0, 0
    for roles in listToPaginate:
        listOfRoles[y][x] = roles
        x += 1
        if x == numOfPageEntries:
            y += 1
            x = 0
    logger.info("[paginate.py paginate()] list added to roles matrix for pagination")
    currentPage = 0
    firstRun = True
    msg = None
    while True:
        logger.info("[paginate.py paginate()] loading page {}".format(currentPage))
        logger.info("[paginate.py paginate()] loading roles {}".format(listOfRoles[currentPage]))
        output = "{}\n\n```".format(title)
        for x in listOfRoles[currentPage]:
            if x != '':
                output += '\t\"{}\"\n'.format(x)
        output += '```{}/{}'.format(str(currentPage + 1), str(numOfPages))
        logger.info("[paginate.py paginate()] created and filled Embed with roles of the current page "
                    + str(currentPage))

        # determining which reactions are needed
        if numOfPages == 1:
            toReactUnicode = [u"\U00002705"]
        else:
            toReactUnicode = [u"\U000023EA", u"\U000023E9", u"\U00002705"]

        if firstRun:
            firstRun = False
            msg = await ctx.send(output)
            logger.info("[paginate.py paginate()] sent message")
        else:
            await msg.edit(content=output)
            await msg.clear_reactions()
            logger.info("[paginate.py paginate()] edited message")

        for reaction in toReactUnicode:
            await msg.add_reaction(reaction)

        logger.info("[paginate.py paginate()] added all reactions to message")

        def checkReaction(reaction, user):
            if not user.bot:
                e = str(reaction.emoji)
                logger.info("[paginate.py paginate()] reaction {} detected from {}".format(e, user))
                return e.startswith(('⏪', '⏩', '✅'))

        userReacted = False
        while userReacted is False:
            try:
                userReacted = await bot.wait_for('reaction_add', timeout=20, check=checkReaction)
            except asyncio.TimeoutError:
                logger.info("[paginate.py paginate()] timed out waiting for the user's reaction.")

            if userReacted:
                if '⏪' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage - 1
                    if currentPage < 0:
                        currentPage = numOfPages - 1
                    logger.info(
                        "[paginate.py paginate()] user indicates "
                        "they want to go back a page from {} to {}".format(prevPage, currentPage)
                    )
                elif '⏩' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage + 1
                    if currentPage == numOfPages:
                        currentPage = 0
                    logger.info(
                        "[paginate.py paginate()] user indicates they want"
                        " to go forward a page from {} to {}".format(prevPage, currentPage)
                    )
                elif '✅' == userReacted[0].emoji:
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
