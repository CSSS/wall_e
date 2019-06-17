# from discord.ext import commands
# import discord
import asyncio
import logging
import helper_files.settings as settings
from helper_files.embed import embed as imported_embed

logger = logging.getLogger('wall_e')


async def paginateEmbed(bot, ctx, descriptionToEmbed, title=" "):
    numOfPages = len(descriptionToEmbed)
    logger.info("[Paginate paginateEmbed()] called with following argument: title=" + title
                + "\n\ndescriptionToEmbed=" + str(descriptionToEmbed) + "\n\n")

    currentPage = 0
    firstRun = True
    msg = None

    while True:
        logger.info("[Paginate paginateEmbed()] loading page " + str(currentPage))
        logger.info("[Paginate paginateEmbed()] loading roles " + str(descriptionToEmbed[currentPage]))

        embedObj = await imported_embed(ctx, title=title, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR,
                                        description=descriptionToEmbed[currentPage], footer='{}/{}'.format(
                                            currentPage + 1, numOfPages))
        if embedObj is not None:
            logger.info("[Paginate paginateEmbed()] embed succesfully created and populated for page "
                        + str(currentPage))
        else:
            return

        # determining which reactions are needed
        if numOfPages == 1:
            toReact = ['✅']
        else:
            toReact = ['⏪', '⏩', '✅']

        # setting the content if it was the first run through or not.
        if firstRun is True:
            firstRun = False
            msg = await ctx.send(content=None, embed=embedObj)
            logger.info("[Paginate paginateEmbed()] sent message")
        else:
            await msg.edit(embed=None)  # this is only here cause there seems to be a bug with editing embeds where
            # it will still retain some traces of the former embed
            await msg.edit(embed=embedObj)
            await msg.clear_reactions()
            logger.info("[Paginate paginateEmbed()] edited message")

        # adding reactions deemed necessary to page
        for reaction in toReact:
            await msg.add_reaction(reaction)

        logger.info("[Paginate paginateEmbed()] added all reactions to message")

        def checkReaction(reaction, user):
            if not user.bot:  # just making sure the bot doesnt take its own reactions
                # into consideration
                e = str(reaction.emoji)
                logger.info("[Paginate paginateEmbed()] reaction " + e + " detected from " + str(user))
                return e.startswith(('⏪', '⏩', '✅'))

        userReacted = False
        while userReacted is False:
            try:
                userReacted = await bot.wait_for('reaction_add', timeout=20, check=checkReaction)
            except asyncio.TimeoutError:
                logger.info("[Paginate paginateEmbed()] timed out waiting for the user's reaction.")

            if userReacted:
                if '⏪' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage - 1
                    if currentPage < 0:
                        currentPage = numOfPages - 1
                    logger.info("[Paginate paginateEmbed()] user indicates they want to go back a page from "
                                + str(prevPage) + " to " + str(currentPage))

                elif '⏩' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage + 1
                    if currentPage == numOfPages:
                        currentPage = 0
                    logger.info("[Paginate paginateEmbed()] user indicates they want to go forward a page from "
                                + str(prevPage) + " to " + str(currentPage))

                elif '✅' == userReacted[0].emoji:
                    logger.info("[Paginate paginateEmbed()] user indicates they are done with the roles command, "
                                + "deleting roles message")
                    await msg.delete()
                    return
            else:
                logger.info("[Paginate paginateEmbed()] deleting message")
                await msg.delete()
                return


async def paginate(bot, ctx, listToPaginate, numOfPages=0, numOfPageEntries=0, title=" "):
    logger.info("[Paginate paginate()] called with following argument: listToPaginate=" + str(listToPaginate)
                + "\n\tnumOfPages=" + str(numOfPages) + ", numOfPageEntries=" + str(numOfPageEntries) + " and title="
                + title)
    if numOfPages == 0:
        if numOfPageEntries == 0:
            logger.info("[Paginate paginate()] you need to specify either \"numOfPages\" or \"numOfPageEntries\"")
            return
        else:
            if int(len(listToPaginate) / numOfPageEntries) == len(listToPaginate) / numOfPageEntries:
                numOfPages = int(len(listToPaginate) / numOfPageEntries)
            else:
                numOfPages = int(len(listToPaginate) / numOfPageEntries) + 1
    else:
        if numOfPageEntries != 0:
            logger.info("[Paginate paginate()] you specified both \"numOfPages\" and \"numOfPageEntries\", please "
                        + "only use one")
        else:
            if int(len(listToPaginate) / numOfPages) == len(listToPaginate) / numOfPages:
                numOfPageEntries = int(len(listToPaginate) / numOfPages)
            else:
                numOfPageEntries = int(len(listToPaginate) / numOfPages) + 1

    logger.info("[Paginate paginate()] numOfPageEntries set to " + str(numOfPageEntries) + " and numOfPages set to "
                + str(numOfPages))
    listOfRoles = [["" for x in range(numOfPageEntries)] for y in range(numOfPages)]
    x, y = 0, 0
    for roles in listToPaginate:
        listOfRoles[y][x] = roles
        x += 1
        if x == numOfPageEntries:
            y += 1
            x = 0
    logger.info("[Paginate paginate()] list added to roles matrix for pagination")
    currentPage = 0
    firstRun = True
    msg = None
    while True:
        logger.info("[Paginate paginate()] loading page " + str(currentPage))
        logger.info("[Paginate paginate()] loading roles " + str(listOfRoles[currentPage]))
        output = title + "\n\n```"
        for x in listOfRoles[currentPage]:
            if x != '':
                output += '\t\"' + str(x) + "\"\n"
        output += '```{}/{}'.format(str(currentPage + 1), str(numOfPages))
        logger.info("[Paginate paginate()] created and filled Embed with roles of the current page "
                    + str(currentPage))

        # determining which reactions are needed
        if numOfPages == 1:
            toReact = ['✅']
        else:
            toReact = ['⏪', '⏩', '✅']

        if firstRun:
            firstRun = False
            msg = await ctx.send(output)
            logger.info("[Paginate paginate()] sent message")
        else:
            await msg.edit(content=output)
            await msg.clear_reactions()
            logger.info("[Paginate paginate()] edited message")

        for reaction in toReact:
            await msg.add_reaction(reaction)

        logger.info("[Paginate paginate()] added all reactions to message")

        def checkReaction(reaction, user):
            if not user.bot:
                e = str(reaction.emoji)
                logger.info("[Paginate paginate()] reaction " + e + " detected from " + str(user))
                return e.startswith(('⏪', '⏩', '✅'))

        userReacted = False
        while userReacted is False:
            try:
                userReacted = await bot.wait_for('reaction_add', timeout=20, check=checkReaction)
            except asyncio.TimeoutError:
                logger.info("[Paginate paginate()] timed out waiting for the user's reaction.")

            if userReacted:
                if '⏪' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage - 1
                    if currentPage < 0:
                        currentPage = numOfPages - 1
                    logger.info("[Paginate paginate()] user indicates they want to go back a page from "
                                + str(prevPage) + " to " + str(currentPage))
                elif '⏩' == userReacted[0].emoji:
                    prevPage = currentPage
                    currentPage = currentPage + 1
                    if currentPage == numOfPages:
                        currentPage = 0
                    logger.info("[Paginate paginate()] user indicates they want to go forward a page from "
                                + str(prevPage) + " to " + str(currentPage))
                elif '✅' == userReacted[0].emoji:
                    logger.info("[Paginate paginate()] user indicates they are done with the roles command, "
                                + "deleting roles message")
                    await msg.delete()
                    return
            else:
                logger.info("[Paginate paginate()] deleting message")
                await msg.delete()
                return
