import datetime
import discord
from discord.ext import commands
import logging
import psycopg2
import re
import sys
import time
import traceback

from resources.utilities.embed import embed as imported_embed

logger = logging.getLogger('wall_e')


def getClassName():
    return "ManageCog"


class ManageCog(commands.Cog):

    def __init__(self, bot, config):
        logger.info("[testenv.py __init__()] initializing the TestCog")
        bot.add_check(self.check_test_environment)
        self.bot = bot
        self.config = config

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        logger.info("[testenv.py debuginfo()] debuginfo command detected from " + str(ctx.message.author))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            fmt = '```You are testing the latest commit of branch or pull request: {0}```'
            await ctx.send(fmt.format(self.config.get_config_value('database', 'BRANCH_NAME')))
        return

    # this command is used by the TEST guild to ensur that each TEST container will only process incoming commands
    # that originate from channels that match the name of their branch
    def check_test_environment(self, ctx):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
            if ctx.message.guild is not None and \
               ctx.channel.name != self.config.get_config_value('basic_config', 'BRANCH_NAME').lower():
                return False
        return True

    ########################################################
    # Function that gets called whenever a commmand      ##
    # gets called, being use for data gathering purposes ##
    ########################################################
    @commands.Cog.listener()
    async def on_command(self, ctx):
        if self.check_test_environment(ctx) and self.config.enabled("database"):
            try:
                host = self.config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME') + '_wall_e_db'
                dbConnectionString = (
                    "dbname='" + self.config.get_config_value('database', 'WALL_E_DB_DBNAME') + "' "
                    "user='" + self.config.get_config_value('database', 'WALL_E_DB_USER') + "'"
                    " host='" + host + "' password"
                    "='" + self.config.get_config_value('database', 'WALL_E_DB_PASSWORD') + "'")
                logger.info(
                    "[main.py on_command()] dbConnectionString=[dbname="
                    "'" + self.config.get_config_value('database', 'WALL_E_DB_DBNAME')
                    + "' user='" + self.config.get_config_value('database', 'WALL_E_DB_USER') + "' "
                    "host='" + host + "' password='******']")
                conn = psycopg2.connect(dbConnectionString)
                logger.info("[main.py on_command()] PostgreSQL connection established")
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                curs = conn.cursor()
                epoch_time = int(time.time())
                now = datetime.datetime.now()
                current_year = str(now.year)
                current_month = str(now.month)
                current_day = str(now.day)
                current_hour = str(now.hour)
                channel_name = str(ctx.channel).replace("\'", "[single_quote]").strip()
                command = str(ctx.command).replace("\'", "[single_quote]").strip()
                method_of_invoke = str(ctx.invoked_with).replace("\'", "[single_quote]").strip()
                invoked_subcommand = str(ctx.invoked_subcommand).replace("\'", "[single_quote]").strip()

                # this next part is just setup to keep inserting until it finsd a primary key that is not in use
                successful = False
                while not successful:
                    try:
                        sqlCommand = ("""INSERT INTO CommandStats ( \"EPOCH TIME\", YEAR, MONTH, DAY, HOUR,
                                      \"Channel Name\", Command, \"Invoked with\",
                                      "Invoked subcommand\") VALUES (""" + str(epoch_time) + """,""" + current_year
                                      + """,""" + current_month + """,""" + current_day + """,""" + current_hour
                                      + """,'""" + channel_name + """', '"""
                                      + command + """','""" + method_of_invoke + """','"""
                                      + invoked_subcommand + """');""")
                        logger.info("[main.py on_command()] sqlCommand=[" + sqlCommand + "]")
                        curs.execute(sqlCommand)
                    except psycopg2.IntegrityError as e:
                        logger.error("[main.py on_command()] enountered following exception when trying to insert the"
                                     " record\n{}".format(e))
                        epoch_time += 1
                        logger.info("[main.py on_command()] incremented the epoch time to " + str(epoch_time) + " and"
                                    " will try again.")
                    else:
                        successful = True
                curs.close()
                conn.close()
            except Exception as e:
                logger.error("[main.py on_command()] enountered following exception when setting up PostgreSQL "
                             "connection\n{}".format(e))

    ####################################################
    # Function that gets called when the script cant ##
    # understand the command that the user invoked   ##
    ####################################################
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if self.check_test_environment(ctx):
            if isinstance(error, commands.MissingRequiredArgument):
                fmt = 'Missing argument: {0}'
                logger.error('[main.py on_command_error()] ' + fmt.format(error.param))
                eObj = await imported_embed(
                    ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=fmt.format(error.param)
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)
            else:
                # only prints out an error to the log if the string that was entered doesnt contain just "."
                pattern = r'[^\.]'
                if re.search(pattern, str(error)[9:-14]):
                    # author = ctx.author.nick or ctx.author.name
                    # await ctx.send('Error:\n```Sorry '+author+', seems like the command
                    # \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    return

    # this command is used by the TEST guild to create the channel from which this TEST container will process
    # commands
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            logger.info(
                "[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels)
            )
            channels = self.bot.guilds[0].channels
            branch_name = self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
            if discord.utils.get(channels, name=branch_name) is None:
                logger.info(
                    "[testenv.py on_ready()] creating the text channel"
                    " " + self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
                    )
                await self.bot.guilds[0].create_text_channel(branch_name)
