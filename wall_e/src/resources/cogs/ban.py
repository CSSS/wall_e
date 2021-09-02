from os import name
from discord.ext import commands
import discord
import asyncio
from resources.utilities.embed import embed as em
import psycopg2
import datetime
import pytz
import re
import logging
logger = logging.getLogger('wall_e')


class Ban(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.blacklist = []

        # establish connection to db
        try:
            # revert this if statement to just host = '{}...'
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
                host = 'localhost'
            else:
                host = '{}_wall_e_db'.format(self.config.get_config_value('basic_config', 'COMPOSE_PROJECT_NAME'))

            db_connection_string = (
                f"dbname='{self.config.get_config_value('database', 'WALL_E_DB_DBNAME')}'"
                f"user='{self.config.get_config_value('database', 'WALL_E_DB_USER')}' host='{host}'"
            )
            logger.info("[Ban __init__] db_connection_string=[{}]".format(db_connection_string))

            conn = psycopg2.connect(
                "{}  password='{}'".format(
                    db_connection_string, self.config.get_config_value('database', 'WALL_E_DB_PASSWORD')
                )
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.curs = conn.cursor()

            self.curs.execute(  "CREATE TABLE IF NOT EXISTS Banned_users ("
                                "username                VARCHAR(32)    NOT NULL,"
                                "user_id                 CHAR(18)       NOT NULL,"
                                "mod                     VARCHAR(32)    NOT NULL,"
                                "mod_id                  CHAR(18)       NOT NULL,"
                                "date                    TIMESTAMPTZ    NOT NULL UNIQUE DEFAULT NOW(),"
                                "reason                  TEXT           NOT NULL,"
                                "latest_join_attempt     TIMESTAMPTZ,"
                                "PRIMARY KEY             (user_id, date)"
                                ")"
                             )

            logger.info("[Ban __init__] PostgreSQL connection established")
        except Exception as e:
            logger.error("[Ban __init__] enountered following exception when setting up PostgreSQL "
                         f"connection\n{e}")

    @commands.Cog.listener(name='on_ready')
    async def load_mod_channel(self):
        self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name="council-summary")

    @commands.command()
    async def ban(self, ctx, *args):
        args = list(args)
        mod_info = [ctx.author.name+'#'+ctx.author.discriminator, ctx.author.id]

        # confirm at least 1 @ mention of user to ban
        if len(ctx.message.mentions) < 1:
            e_obj = await em(ctx=ctx, title="Invalid Arguments",
                             author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                             avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                             content=[("Error", "Please @ mention the user(s) to ban")], colour=0xA6192E,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # get mentions
        users_to_ban = ctx.message.mentions

        # construct reason, but first remove @'s from the args
        reason = ''.join([i for i in args if not re.match(r'<@!?[0-9]*>', i)])
        reason = reason if reason else "No Reason Given!"
        print(f"reason {reason}")

        # get user info for db
        user_info = [[user.name+'#'+user.discriminator, user.id] for user in users_to_ban]

        # ban
        dm = True
        for user in users_to_ban:
            # dm banned user
            e_obj = await em(ctx, title="Banned", content=[("You've been banned from", ctx.guild.name)])
            try:
                if e_obj:
                    await user.send(embed=e_obj)
            except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
                dm = False

            # kick
            await user.kick(reason=reason)

            # report to council
            e_obj = await em(ctx, title="Ban Hammer Deployed",
                             author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                             avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                             content=[
                                        ("Banned User", f"{user.name}#{user.discriminator}"),
                                        ("Ban Reason", reason),
                                        ("Moderator", f"{ctx.author.nick} [ {mod_info[0]} ]"),
                                        ("Notification DM Sent", "SENT" if dm else "NOT SENT, DUE TO USER DM PREF's")
                                     ],
                             footer="Moderator action")
            if e_obj:
                await self.mod_channel.send(embed=e_obj)

        # update db


    # @commands.command()
    # async def ban_history(self, ctx, mention: discord.Member):
    #     print('getting history')
    #     await ctx.send('history!')

    # @commands.Cog.listener(name='on_member_join')
    # async def blacklist_watch(self, member):
    #     print(f"someone joined idk: {member}")
