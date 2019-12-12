from discord.ext import commands
import discord
import subprocess
import logging
import asyncio
from resources.utilities.send import send as helper_send
import importlib
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt # noqa
import numpy as np # noqa
import psycopg2 # noqa

logger = logging.getLogger('wall_e')


def getClassName():
    return "Administration"


class Administration(commands.Cog):

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot

    def validCog(self, name):
        for cog in self.config.get_cogs():
            if cog["name"] == name:
                return True, cog["path"]
        return False, ''

    @commands.command()
    async def exit(self, ctx):
        if 'LOCALHOST' == self.config.get_config_value('basic_config', 'ENVIRONMENT'):
            await self.bot.close()

    @commands.command()
    async def load(self, ctx, name):
        logger.info("[Administration load()] load command detected from {}".format(ctx.message.author))
        if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
            logger.info("[Administration load()] {} successfully authenticated".format(ctx.message.author))
            valid, folder = self.validCog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info(
                    "[Administration load()] {} tried loading "
                    "{} which doesn't exist.".format(ctx.message.author, name)
                )
                return
            try:
                cogToLoad = importlib.import_module(folder+name)
                cogFile = getattr(cogToLoad, str(cogToLoad.getClassName()))
                self.bot.add_cog(cogFile(self.bot, self.config))
                await ctx.send("{} command loaded.".format(name))
                logger.info("[Administration load()] {} has been successfully loaded".format(name))
            except(AttributeError, ImportError) as e:
                await ctx.send("command load failed: {}, {}".format(type(e), str(e)))
                logger.info("[Administration load()] loading {} failed :{}, {}".format(name, type(e), e))
        else:
            logger.info(
                "[Administration load()] unauthorized command attempt detected from {}".format(ctx.message.author)
            )
            await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

    @commands.command()
    async def unload(self, ctx, name):
        logger.info("[Administration unload()] unload command detected from {}".format(ctx.message.author))
        if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
            logger.info("[Administration unload()] {} successfully authenticated".format(ctx.message.author))
            valid, folder = self.validCog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info(
                    "[Administration load()] {} tried loading "
                    "{} which doesn't exist.".format(ctx.message.author, name)
                )
                return
            cogToUnload = importlib.import_module(folder+name)
            self.bot.remove_cog(cogToUnload.getClassName())
            await ctx.send("{} command unloaded".format(name))
            logger.info("[Administration unload()] {} has been successfully loaded".format(name))
        else:
            logger.info("[Administration unload()] unauthorized "
                        "command attempt detected from {}".format(ctx.message.author))
            await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

    @commands.command()
    async def reload(self, ctx, name):
        logger.info("[Administration reload()] reload command detected from {}".format(ctx.message.author))
        if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
            logger.info("[Administration reload()] {} successfully authenticated".format(ctx.message.author))
            valid, folder = self.validCog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info("[Administration reload()] {} tried "
                            "loading {} which doesn't exist.".format(ctx.message.author, name))
                return
            cogToReload = importlib.import_module(folder+name)
            self.bot.remove_cog(cogToReload.getClassName())
            try:
                cogFile = getattr(cogToReload, cogToReload.getClassName())
                self.bot.add_cog(cogFile(self.bot, self.config))
                await ctx.send("`{} command reloaded`".format(folder + name))
                logger.info("[Administration reload()] {} has been successfully reloaded".format(name))
            except(AttributeError, ImportError) as e:
                await ctx.send("Command load failed: {}, {}".format(type(e), str(e)))
                logger.info("[Administration reload()] loading {} failed :{}, {}".format(name, type(e), e))
        else:
            logger.info("[Administration reload()] unauthorized "
                        "command attempt detected from {}".format(ctx.message.author))
            await ctx.send("You do not have adequate permission "
                           "to execute this command, incident will be reported")

    @commands.command()
    async def exc(self, ctx, *args):
        logger.info("[Administration exc()] exc command detected "
                    "from {} with arguments {}".format(ctx.message.author, " ".join(args)))
        if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
            logger.info("[Administration exc()] {} successfully authenticated".format(ctx.message.author))
            query = " ".join(args)
            # this got implemented for cases when the output of the command is too big to send to the channel
            exitCode, output = subprocess.getstatusoutput(query)
            await helper_send(ctx, "Exit Code: {}".format(exitCode))
            await helper_send(ctx, output, prefix="```", suffix="```")
        else:
            logger.info("[Administration exc()] unauthorized "
                        "command attempt detected from {}".format(ctx.message.author))
            await ctx.send("You do not have adequate permission "
                           "to execute this command, incident will be reported")

    def get_column_headers_from_database(self):
        dbConn = self.connect_to_database()
        if dbConn is not None:
            dbCurr = dbConn.cursor()
            dbCurr.execute("Select * FROM commandstats LIMIT 0")
            colnames = [desc[0] for desc in dbCurr.description]
            dbCurr.close()
            dbConn.close()
            return [name.strip() for name in colnames]
        else:
            return None

    def determine_x_y_frequency(self, dbConn, filters=None):
        conn = dbConn
        if conn is None:
            return None
        dbCurr = conn.cursor()
        logger.info("[Administration determine_x_y_frequency()] trying to "
                    "create a dictionary from {} with the filters:\n\t{}".format(dbCurr, filters))
        combinedFilter = '", "'.join(str(e) for e in filters)
        combinedFilter = "\"{}\"".format(combinedFilter)
        sqlQuery = "select {} from commandstats;".format(combinedFilter)
        logger.info("[Administration determine_x_y_frequency()] initial sql query to determine what entries needs to be"
                    " created with the filter specified above:\n\t{}".format(sqlQuery))
        dbCurr.execute(sqlQuery)
        # getting all the rows that need to be graphed
        results = dbCurr.fetchall()
        # where clause that will be used to determine what remaining rows still need to be added to the dictionary of
        # results
        overarchingWHereClause = ''
        # dictionary that will contain the stats that need to be graphed
        frequency = {}
        index = 0
        # this loop will go through eachu unqiue entry that were turned from the results variable above to determine
        # how much each unique entry
        # was appeared and needs that info added to frequency dictionary
        while len(results) > 0:
            logger.info("[Administration determine_x_y_frequency()] "
                        "{}th index results of sql query=[{}]".format(index, results[0]))
            whereClause = ''  # where clause that keeps track of things that need to be added to the
            # overarchingWhereClause
            entry = ''
            for idx, val in enumerate(filters):
                if len(filters) == 1 + idx:
                    entry += str(results[0][idx])
                    whereClause += "\"{}\"='{}'".format(val, results[0][idx])
                else:
                    entry += '{}_'.format(results[0][idx])
                    whereClause += "\"{}\"='{}' AND ".format(val, results[0][idx])
            logger.info(
                "[Administration determine_x_y_frequency()] where clause for determining which "
                "entries match the entry [{}]:\n\t{}".format(entry, whereClause)
            )
            sqlQuery = "select {} from commandstats WHERE {};".format(combinedFilter, whereClause)
            logger.info(
                "[Administration determine_x_y_frequency()] query that includes the above specified where "
                "clause for determining how many elements match the filter of [{}]:\n\t{}".format(entry, sqlQuery)
            )
            dbCurr.execute(sqlQuery)
            resultsOfQueryForSpecificEntry = dbCurr.fetchall()
            frequency[entry] = len(resultsOfQueryForSpecificEntry)
            logger.info(
                "[Administration determine_x_y_frequency()] determined that {} "
                "entries exist for filter {}".format(frequency[entry], entry)
            )
            if index > 0:
                overarchingWHereClause += ' AND NOT ( {} )'.format(whereClause)
            else:
                overarchingWHereClause += ' NOT ( {} )'.format(whereClause)
            logger.info("[Administration determine_x_y_frequency()] updated where clause for discriminating against all "
                        "entries that have already been recorded:\n\t{}".format(overarchingWHereClause))
            sqlQuery = "select {} from commandstats WHERE ({});".format(combinedFilter, overarchingWHereClause)
            logger.info("[Administration determine_x_y_frequency()] updated sql query to determine what remaining "
                        "entries potentially need to be created after ruling out entries that match the where clause"
                        ":\n\t{}".format(sqlQuery))
            dbCurr.execute(sqlQuery)
            results = dbCurr.fetchall()
            index += 1
        dbCurr.close()
        dbConn.close()
        return frequency

    def connect_to_database(self):
        try:
            host = '{}_wall_e_db'.format(self.config.get_config_value("wall_e", "COMPOSE_PROJECT_NAME"))
            wall_e_db_dbname = self.config.get_config_value('database', 'WALL_E_DB_DBNAME')
            wall_e_db_user = self.config.get_config_value('database', 'WALL_E_DB_USER')
            wall_e_db_password = self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')

            dbConnectionString = ("dbname='{}' user='{}' "
                                  "host='{}'".format(wall_e_db_dbname, wall_e_db_user, host))
            logger.info("[Administration connect_to_database()] dbConnectionString=[{}]".format(dbConnectionString))
            conn = psycopg2.connect("{} password='{}'".format(dbConnectionString, wall_e_db_password))
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("[Administration connect_to_database()] PostgreSQL connection established")
            return conn
        except Exception as e:
            logger.error("[Administration connect_to_database()] enountered following exception when setting up "
                         "PostgreSQL connection\n{}".format(e))
            return None

    @commands.command()
    async def frequency(self, ctx, *args):
        if self.config.enabled("database", option="DB_ENABLED"):
            logger.info("[Administration frequency()] frequency command "
                        "detected from {} with arguments [{}]".format(ctx.message.author, args))
            if len(args) == 0:
                conn = self.get_column_headers_from_database()
                if conn is None:
                    logger.info("[Administration frequency()] unable to connect to the database")
                    await ctx.send("unable to connect to the database")
                else:
                    await ctx.send("please specify which columns you want to count="
                                   + str(list(conn)))
                return
            else:
                dicResult = self.determine_x_y_frequency(self.connect_to_database(), args)
                if dicResult is None:
                    logger.info("[Administration frequency()] unable to connect to the database")
                    await ctx.send("unable to connect to the database")
                    return
            dicResult = sorted(dicResult.items(), key=lambda kv: kv[1])
            logger.info("[Administration frequency()] sorted dicResults by value")
            if len(dicResult) <= 50:
                logger.info("[Administration frequency()] dicResults's length is <= 50")
                labels = [i[0] for i in dicResult]
                numbers = [i[1] for i in dicResult]
                plt.rcdefaults()
                fig, ax = plt.subplots()
                y_pos = np.arange(len(labels))
                for i, v in enumerate(numbers):
                    ax.text(v, i + .25, str(v), color='blue', fontweight='bold')
                ax.barh(y_pos, numbers, align='center', color='green')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels)
                ax.invert_yaxis()  # labels read top-to-bottom
                if len(args) > 1:
                    title = '_'.join(str(arg) for arg in args[:len(args) - 1])
                    title += "_{}".format(args[len(args) - 1])
                else:
                    title = args[0]
                ax.set_title("How may times each {} appears in the database since Sept 21, 2018".format(title))
                fig.set_size_inches(18.5, 10.5)
                fig.savefig('image.png')
                logger.info("[Administration frequency()] graph created and saved")
                plt.close(fig)
                await ctx.send(file=discord.File('image.png'))
                logger.info("[Administration frequency()] graph image file has been sent")
            else:
                logger.info("[Administration frequency()] dicResults's length is > 50")
                numberOfPages = int(len(dicResult) / 50)
                if len(dicResult) % 50 != 0:
                    numberOfPages += 1
                numOfBarsPerPage = int(len(dicResult) / numberOfPages) + 1
                firstIndex, lastIndex = 0, numOfBarsPerPage - 1
                msg = None
                currentPage = 0
                while firstIndex < len(dicResult):
                    logger.info("[Administration frequency()] creating "
                                "a graph with entries {} to {}".format(firstIndex, lastIndex))
                    toReact = ['⏪', '⏩', '✅']
                    labels = [i[0] for i in dicResult][firstIndex:lastIndex]
                    numbers = [i[1] for i in dicResult][firstIndex:lastIndex]
                    plt.rcdefaults()
                    fig, ax = plt.subplots()
                    y_pos = np.arange(len(labels))
                    for i, v in enumerate(numbers):
                        ax.text(v, i + .25, str(v), color='blue', fontweight='bold')
                    ax.barh(y_pos, numbers, align='center', color='green')
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(labels)
                    ax.invert_yaxis()  # labels read top-to-bottom
                    ax.set_xlabel("Page {}/{}".format(currentPage, numberOfPages - 1))
                    if len(args) > 1:
                        title = '_'.join(str(arg) for arg in args[:len(args) - 1])
                        title += "_{}".format(args[len(args) - 1])
                    else:
                        title = args[0]
                    ax.set_title("How may times each {} appears in the database since Sept 21, 2018".format(title))
                    fig.set_size_inches(18.5, 10.5)
                    fig.savefig('image.png')
                    logger.info("[Administration frequency()] graph created and saved")
                    plt.close(fig)
                    if msg is None:
                        msg = await ctx.send(file=discord.File('image.png'))
                    else:
                        await msg.delete()
                        msg = await ctx.send(file=discord.File('image.png'))
                    for reaction in toReact:
                        await msg.add_reaction(reaction)

                    def checkReaction(reaction, user):
                        if not user.bot:  # just making sure the bot doesnt take its own reactions
                            # into consideration
                            e = str(reaction.emoji)
                            logger.info("[Administration frequency()] reaction {} detected from {}".format(e, user))
                            return e.startswith(('⏪', '⏩', '✅'))

                    logger.info("[Administration frequency()] graph image file has been sent")
                    userReacted = False
                    while userReacted is False:
                        try:
                            userReacted = await self.bot.wait_for('reaction_add', timeout=20, check=checkReaction)
                        except asyncio.TimeoutError:
                            logger.info("[Administration frequency()] timed out waiting for the user's reaction.")
                        if userReacted:
                            if '⏪' == userReacted[0].emoji:
                                firstIndex -= numOfBarsPerPage
                                lastIndex -= numOfBarsPerPage
                                currentPage -= 1
                                if firstIndex < 0:
                                    firstIndex, lastIndex = numOfBarsPerPage * 3, numOfBarsPerPage * 4
                                    currentPage = numberOfPages - 1
                                logger.info("[Administration frequency()] user indicates they "
                                            " want to go back to page "
                                            + str(currentPage))
                            elif '⏩' == userReacted[0].emoji:
                                firstIndex += numOfBarsPerPage
                                lastIndex += numOfBarsPerPage
                                currentPage += 1
                                if firstIndex > len(dicResult):
                                    firstIndex, lastIndex = 0, numOfBarsPerPage
                                    currentPage = 0
                                logger.info("[Administration frequency()] user indicates they want to go to page "
                                            + str(currentPage))
                            elif '✅' == userReacted[0].emoji:
                                logger.info("[Administration frequency()] user "
                                            "indicates they are done with the roles "
                                            "command, deleting roles message")
                                await msg.delete()
                                return
                        else:
                            logger.info("[Administration frequency()] deleting message")
                            await msg.delete()
                            return
                    logger.info("[Administration frequency()] updating firstIndex "
                                "and lastIndex to {} and {} respectively".format(firstIndex, lastIndex))
