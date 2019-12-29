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


def get_class_name():
    return "Administration"


class Administration(commands.Cog):

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot

    def valid_cog(self, name):
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
            valid, folder = self.valid_cog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info(
                    "[Administration load()] {} tried loading "
                    "{} which doesn't exist.".format(ctx.message.author, name)
                )
                return
            try:
                cog_to_load = importlib.import_module(folder+name)
                cog_file = getattr(cog_to_load, str(cog_to_load.get_class_name()))
                self.bot.add_cog(cog_file(self.bot, self.config))
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
            valid, folder = self.valid_cog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info(
                    "[Administration load()] {} tried loading "
                    "{} which doesn't exist.".format(ctx.message.author, name)
                )
                return
            cog_to_unload = importlib.import_module(folder+name)
            self.bot.remove_cog(cog_to_unload.get_class_name())
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
            valid, folder = self.valid_cog(name)
            if not valid:
                await ctx.send("```{} isn't a real cog```".format(name))
                logger.info("[Administration reload()] {} tried "
                            "loading {} which doesn't exist.".format(ctx.message.author, name))
                return
            cog_to_reload = importlib.import_module(folder+name)
            self.bot.remove_cog(cog_to_reload.get_class_name())
            try:
                cog_file = getattr(cog_to_reload, cog_to_reload.get_class_name())
                self.bot.add_cog(cog_file(self.bot, self.config))
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
            exit_code, output = subprocess.getstatusoutput(query)
            await helper_send(ctx, "Exit Code: {}".format(exit_code))
            await helper_send(ctx, output, prefix="```", suffix="```")
        else:
            logger.info("[Administration exc()] unauthorized "
                        "command attempt detected from {}".format(ctx.message.author))
            await ctx.send("You do not have adequate permission "
                           "to execute this command, incident will be reported")

    def get_column_headers_from_database(self):
        db_conn = self.connect_to_database()
        if db_conn is not None:
            db_curr = db_conn.cursor()
            db_curr.execute("Select * FROM commandstats LIMIT 0")
            colnames = [desc[0] for desc in db_curr.description]
            db_curr.close()
            db_conn.close()
            return [name.strip() for name in colnames]
        else:
            return None

    def determine_x_y_frequency(self, db_conn, filters=None):
        conn = db_conn
        if conn is None:
            return None
        db_curr = conn.cursor()
        logger.info("[Administration determine_x_y_frequency()] trying to "
                    "create a dictionary from {} with the filters:\n\t{}".format(db_curr, filters))
        combined_filter = '", "'.join(str(e) for e in filters)
        combined_filter = "\"{}\"".format(combined_filter)
        sql_query = "select {} from commandstats;".format(combined_filter)
        logger.info("[Administration determine_x_y_frequency()] initial "
                    "sql query to determine what entries needs to be"
                    " created with the filter specified above:\n\t{}".format(sql_query))
        db_curr.execute(sql_query)
        # getting all the rows that need to be graphed
        results = db_curr.fetchall()
        # where clause that will be used to determine what remaining rows still need to be added to the dictionary of
        # results
        overarching_where_clause = ''
        # dictionary that will contain the stats that need to be graphed
        frequency = {}
        index = 0
        # this loop will go through eachu unqiue entry that were turned from the results variable above to determine
        # how much each unique entry
        # was appeared and needs that info added to frequency dictionary
        while len(results) > 0:
            logger.info("[Administration determine_x_y_frequency()] "
                        "{}th index results of sql query=[{}]".format(index, results[0]))
            where_clause = ''  # where clause that keeps track of things that need to be added to the
            # overarchingWhereClause
            entry = ''
            for idx, val in enumerate(filters):
                if len(filters) == 1 + idx:
                    entry += str(results[0][idx])
                    where_clause += "\"{}\"='{}'".format(val, results[0][idx])
                else:
                    entry += '{}_'.format(results[0][idx])
                    where_clause += "\"{}\"='{}' AND ".format(val, results[0][idx])
            logger.info(
                "[Administration determine_x_y_frequency()] where clause for determining which "
                "entries match the entry [{}]:\n\t{}".format(entry, where_clause)
            )
            sql_query = "select {} from commandstats WHERE {};".format(combined_filter, where_clause)
            logger.info(
                "[Administration determine_x_y_frequency()] query that includes the above specified where "
                "clause for determining how many elements match the filter of [{}]:\n\t{}".format(entry, sql_query)
            )
            db_curr.execute(sql_query)
            results_of_query_for_specific_entry = db_curr.fetchall()
            frequency[entry] = len(results_of_query_for_specific_entry)
            logger.info(
                "[Administration determine_x_y_frequency()] determined that {} "
                "entries exist for filter {}".format(frequency[entry], entry)
            )
            if index > 0:
                overarching_where_clause += ' AND NOT ( {} )'.format(where_clause)
            else:
                overarching_where_clause += ' NOT ( {} )'.format(where_clause)
            logger.info("[Administration determine_x_y_frequency()] "
                        "updated where clause for discriminating against all "
                        "entries that have already been recorded:\n\t{}".format(overarching_where_clause))
            sql_query = "select {} from commandstats WHERE ({});".format(combined_filter, overarching_where_clause)
            logger.info("[Administration determine_x_y_frequency()] updated sql query to determine what remaining "
                        "entries potentially need to be created after ruling out entries that match the where clause"
                        ":\n\t{}".format(sql_query))
            db_curr.execute(sql_query)
            results = db_curr.fetchall()
            index += 1
        db_curr.close()
        db_conn.close()
        return frequency

    def connect_to_database(self):
        try:
            host = '{}_wall_e_db'.format(self.config.get_config_value("basic_config", "COMPOSE_PROJECT_NAME"))
            wall_e_db_dbname = self.config.get_config_value('database', 'WALL_E_DB_DBNAME')
            wall_e_db_user = self.config.get_config_value('database', 'WALL_E_DB_USER')
            wall_e_db_password = self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')

            db_connection_string = (
                "dbname='{}' user='{}' host='{}'".format(
                    wall_e_db_dbname,
                    wall_e_db_user,
                    host
                )
            )
            logger.info(
                "[Administration connect_to_database()] db_connection_string=[{}]".format(
                    db_connection_string
                )
            )
            conn = psycopg2.connect("{} password='{}'".format(db_connection_string, wall_e_db_password))
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
                dic_result = self.determine_x_y_frequency(self.connect_to_database(), args)
                if dic_result is None:
                    logger.info("[Administration frequency()] unable to connect to the database")
                    await ctx.send("unable to connect to the database")
                    return
            dic_result = sorted(dic_result.items(), key=lambda kv: kv[1])
            logger.info("[Administration frequency()] sorted dicResults by value")
            if len(dic_result) <= 50:
                logger.info("[Administration frequency()] dicResults's length is <= 50")
                labels = [i[0] for i in dic_result]
                numbers = [i[1] for i in dic_result]
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
                number_of_pages = int(len(dic_result) / 50)
                if len(dic_result) % 50 != 0:
                    number_of_pages += 1
                number_of_bars_per_page = int(len(dic_result) / number_of_pages) + 1
                first_index, last_index = 0, number_of_bars_per_page - 1
                msg = None
                current_page = 0
                while first_index < len(dic_result):
                    logger.info("[Administration frequency()] creating "
                                "a graph with entries {} to {}".format(first_index, last_index))
                    to_react = ['⏪', '⏩', '✅']
                    labels = [i[0] for i in dic_result][first_index:last_index]
                    numbers = [i[1] for i in dic_result][first_index:last_index]
                    plt.rcdefaults()
                    fig, ax = plt.subplots()
                    y_pos = np.arange(len(labels))
                    for i, v in enumerate(numbers):
                        ax.text(v, i + .25, str(v), color='blue', fontweight='bold')
                    ax.barh(y_pos, numbers, align='center', color='green')
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(labels)
                    ax.invert_yaxis()  # labels read top-to-bottom
                    ax.set_xlabel("Page {}/{}".format(current_page, number_of_pages - 1))
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
                    for reaction in to_react:
                        await msg.add_reaction(reaction)

                    def check_reaction(reaction, user):
                        if not user.bot:  # just making sure the bot doesnt take its own reactions
                            # into consideration
                            e = str(reaction.emoji)
                            logger.info("[Administration frequency()] reaction {} detected from {}".format(e, user))
                            return e.startswith(('⏪', '⏩', '✅'))

                    logger.info("[Administration frequency()] graph image file has been sent")
                    user_reacted = False
                    while user_reacted is False:
                        try:
                            user_reacted = await self.bot.wait_for('reaction_add', timeout=20, check=check_reaction)
                        except asyncio.TimeoutError:
                            logger.info("[Administration frequency()] timed out waiting for the user's reaction.")
                        if user_reacted:
                            if '⏪' == user_reacted[0].emoji:
                                first_index -= number_of_bars_per_page
                                last_index -= number_of_bars_per_page
                                current_page -= 1
                                if first_index < 0:
                                    first_index, last_index = number_of_bars_per_page * 3, number_of_bars_per_page * 4
                                    current_page = number_of_pages - 1
                                logger.info("[Administration frequency()] user indicates they "
                                            " want to go back to page "
                                            + str(current_page))
                            elif '⏩' == user_reacted[0].emoji:
                                first_index += number_of_bars_per_page
                                last_index += number_of_bars_per_page
                                current_page += 1
                                if first_index > len(dic_result):
                                    first_index, last_index = 0, number_of_bars_per_page
                                    current_page = 0
                                logger.info("[Administration frequency()] user indicates they want to go to page "
                                            + str(current_page))
                            elif '✅' == user_reacted[0].emoji:
                                logger.info("[Administration frequency()] user "
                                            "indicates they are done with the roles "
                                            "command, deleting roles message")
                                await msg.delete()
                                return
                        else:
                            logger.info("[Administration frequency()] deleting message")
                            await msg.delete()
                            return
                    logger.info("[Administration frequency()] updating first_index "
                                "and last_index to {} and {} respectively".format(first_index, last_index))
