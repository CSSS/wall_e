from os import name
from discord.ext import commands
import discord
import asyncio
from resources.utilities.embed import embed as em
import psycopg2
import datetime
import logging
logger = logging.getLogger('wall_e')


class Ban(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.blacklist = []

        # establish connection to db
        # try:
        #     if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
        #         host = 'localhost'
        #     else:
        #         host = '{}_wall_e_db'.format(self.config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME'))

        #     db_connection_string = (
        #         f"dbname='{self.config.get_config_value('database', 'WALL_E_DB_DBNAME')}'"
        #         f"user='{self.config.get_config_value('database', 'WALL_E_DB_USER')}' host='{host}'"
        #     )
        #     logger.info("[Ban __init__] db_connection_string=[{}]".format(db_connection_string))

        #     conn = psycopg2.connect(
        #         "{}  password='{}'".format(
        #             db_connection_string, self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')
        #         )
        #     )
        #     conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        #     self.curs = conn.cursor()
        #     self.curs.execute('CREATE TABLE FOR BANNED USERS')
        #     logger.info("[Ban __init__] PostgreSQL connection established")
        # except Exception as e:
        #     logger.error("[Ban __init__] enountered following exception when setting up PostgreSQL "
        #                  f"connection\n{e}")

    @commands.command()
    async def ban(self, ctx, mention: discord.Member, reason=None):
        print('banned lul')
        print(mention)
        print(type(mention))
        await ctx.send("something happened i guess")

    @commands.command()
    async def ban_history(self, ctx, mention: discord.Member):
        print('getting history')
        await ctx.send('history!')

    @ban.error
    @ban_history.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send('I could not find that member...')






    # @commands.Cog.listener(name='on_member_join')
    # async def blacklist_watch(self, member):
    #     print(f"someone joined idk: {member}")