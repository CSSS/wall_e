from discord.ext import commands
import discord
from resources.utilities.embed import embed as em
import psycopg2
import datetime
import pytz
import re
from typing import Union
import logging
logger = logging.getLogger('wall_e')


class Ban(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.blacklist = []
        self.datetime = datetime.datetime
        self.errorColour = 0xA6192E

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
                                "username    VARCHAR(32) NOT NULL,"
                                "user_id     CHAR(18),"
                                "PRIMARY KEY (user_id)"
                                ")"
                             )

            self.curs.execute(  "CREATE TABLE IF NOT EXISTS Ban_records ("
                                "ban_id                  INTEGER GENERATED ALWAYS AS IDENTITY,"
                                "username                VARCHAR(32)    NOT NULL,"
                                "user_id                 CHAR(18)       NOT NULL,"
                                "mod                     VARCHAR(32),"
                                "mod_id                  CHAR(18),"
                                "date                    TIMESTAMPTZ    UNIQUE,"
                                "reason                  TEXT           NOT NULL,"
                                "UNIQUE (user_id, date),"
                                "PRIMARY KEY (ban_id)"
                                ")"
                             )

            logger.info("[Ban __init__] PostgreSQL connection established")
        except Exception as e:
            logger.error("[Ban __init__] encountered following exception when setting up PostgreSQL "
                         f"connection\n{e}")

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name="council-summary")

        # read in blacklist of banned users
        try:
            self.curs.execute("SELECT user_id FROM Banned_users;")
        except Exception as e:
            print(f"sql exception: {e}")

        bans = self.curs.fetchall()
        self.blacklist = [int(ban[0]) for ban in bans]

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        if member.id in self.blacklist:
            await member.send(f"You were banned from {self.bot.guilds[0]}")
            await member.kick(reason="Not allowed back on server.")

    @commands.Cog.listener(name='on_member_ban')
    async def intercept(self, guild: discord.Guild, member: Union[discord.User, discord.Member]):
        # need to read the audit log to grab mod, date, and reason
        try:
            audit_ban = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
        except Exception as e:
            print(f'error while fetching ban data: {e}')
            return
        audit_ban = audit_ban[0]

        # name, id, mod, mod id, date, reason
        username = member.name + '#' + member.discriminator
        mod = audit_ban.user.name+ '#' + audit_ban.user.discriminator
        mod_id = audit_ban.user.id
        date = audit_ban.created_at
        reason = audit_ban.reason if audit_ban.reason else 'No Reason Given!'

        # update blacklist and db
        self.blacklist.append(member.id)
        await self.insert_ban(username, member.id)
        await self.insert_record(username, member.id, mod, mod_id, date, reason)

        # unban
        await self.bot.guilds[0].unban(member)

        # can't dm once they're not in guild

    async def insert_ban(self, username, user_id):
        try:
            self.curs.execute("INSERT INTO Banned_users VAlUES (%s, %s)", (username, user_id))
        except Exception as e:
            print(f'sql error: {e}')

    async def insert_record(self, username, user_id, mod, mod_id, date, reason):
        query = "INSERT INTO Ban_records (username, user_id, mod, mod_id, date, reason) " \
              "VALUES (%s, %s, %s, %s, %s, %s)"
        try:
            self.curs.execute(query, (username, user_id, mod, mod_id, date, reason))
        except Exception as e:
            print(f'sql error {e}')

    @commands.command()
    async def initban(self, ctx):
        try:
            audit_logs = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
            bans = await self.bot.guilds[0].bans()
        except Exception as e:
            print(f'error while fetching ban data: {e}')

        ban_ids = [ban.user.id for ban in bans]
        ban_data = []
        audit_users = []
        for ban in audit_logs:
            audit_users.append( ban.target.id )

            ban_data.append([   ban.target.name+'#'+ban.target.discriminator,
                                ban.target.id,
                                ban.user.name+'#'+ban.user.discriminator,
                                ban.user.id,
                                ban.created_at,
                                ban.reason if ban.reason else 'No Reason Given!'
                            ])

        for ban in bans:
            if ban.user.id in audit_users:
                continue
            ban_data.append([   ban.user.name+'#'+ban.user.discriminator,
                                ban.user.id,
                                None,
                                None,
                                None,
                                'No Reason Given!'
                            ])

        # push to db and blacklist
        for ban in ban_data:
            if ban[1] in ban_ids:
                self.blacklist.append( ban[1] )
                await self.insert_ban(ban[0], ban[1])

            await self.insert_record(ban[0], ban[1], ban[2], ban[3], ban[4], ban[5])

    @commands.command()
    async def ban(self, ctx, *args):
        args = list(args)
        mod_info = [ctx.author.name+'#'+ctx.author.discriminator, ctx.author.id]

        # confirm at least 1 @ mention of user to ban
        if len(ctx.message.mentions) < 1:
            e_obj = await em(ctx=ctx, title="Invalid Arguments",
                             content=[("Error", "Please @ mention the user(s) to ban")], colour=0xA6192E,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # get mentions
        users_to_ban = ctx.message.mentions

        # construct reason, but first remove @'s from the args
        reason = ''.join([i+' ' for i in args if not re.match(r'<@!?[0-9]*>', i)])
        reason = reason if reason else "No Reason Given!"

        # ban
        dm = True
        for user in users_to_ban:
            # add to blacklist
            self.blacklist.append( user.id )
            username = user.name + '#' + user.discriminator

            # dm banned user
            e_obj = discord.Embed(title="Ban Notification",
                                  description=f"**You've been PERMANENTLY BANNED from"+
                                               f"{self.bot.guilds[0].name.upper()}.**",
                                  color=discord.Color.red(),
                                  timestamp=self.datetime.now(pytz.timezone('Canada/Pacific')))

            e_obj.add_field(name='Reason',
                            value=f"```{reason}```\n"+
                                   "Please refrain from this kind of behaviour in the future. Thank you.")

            e_obj.set_footer(icon_url=self.bot.guilds[0].icon_url, text=self.bot.guilds[0])
            try:
                if e_obj:
                    await user.send(embed=e_obj)
            except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
                dm = False

            # kick
            await user.kick(reason=reason)
            dt = self.datetime.now(pytz.utc)

            # report to council
            e_obj = await em(ctx, title="Ban Hammer Deployed",
                             colour=discord.Color.red(),
                             content=[
                                        ("Banned User", username),
                                        ("Ban Reason", reason),
                                        ("Moderator", f"**{mod_info[0]}** [ {mod_info[1]} ]"),
                                        ("Notification DM Sent", "SENT" if dm else "NOT SENT, DUE TO USER DM PREF's")
                                     ],
                             footer="Moderator action")
            if e_obj:
                await self.mod_channel.send(embed=e_obj)

            # update db
            await self.insert_ban(username, user.id)
            await self.insert_record(username, user.id, mod_info[0], mod_info[1], dt, reason)

    @commands.command()
    async def bans(self, ctx):
        try:
            self.curs.execute("SELECT * FROM banned_users;")
        except Exception as e:
            print(f"error encountered during sql query: {e}")
            await ctx.send(f"Encountered the following sql error: {e}")
            return

        rows = self.curs.fetchall()

        emb = discord.Embed(title="Banned members", color=discord.Color.red())

        names =""
        ids = ""
        for row in rows:
            name = row[0]
            _id = row[1]
            if len(names) + len(name) > 1024 or len(ids) + len(_id) > 1024:
                emb.add_field(name="Names", value=names, inline=True)
                emb.add_field(name="IDs", value=ids, inline=True)
                await ctx.send(embed=emb)
                emb.clear_fields()
                names = ""
                ids = ""

            names += f"{name}\n"
            ids += f"{_id}\n"

        # send out the last bit, if not empy
        if names:
            emb.add_field(name="Names", value=names, inline=True)
            emb.add_field(name="IDs", value=ids, inline=True)
            await ctx.send(embed=emb)

    @commands.command()
    async def unban(self, ctx, _id: int):
        if _id not in self.blacklist:
            e_obj = await em(ctx, title="Error",
                             content=[("Problem",
                                       f"`{_id}` is either not a valid Discord ID **OR** is not a banned user.")],
                             colour=self.errorColour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # "unban"
        self.blacklist.remove(_id)

        try:
            self.curs.execute("SELECT username FROM Banned_users WHERE user_id='%s'", [_id])
            name = self.curs.fetchone()[0]
            self.curs.execute("DELETE FROM Banned_users WHERE user_id='%s';", [_id])
        except Exception as e:
            print(f'sql exception: {e}')
            await ctx.send(f"Encountered the following sql error: {e}")
            return

        e_obj = await em(ctx, title="Unban", description=f"**`{name}`** was unbanned.", colour=discord.Color.red())
        if e_obj:
            await self.mod_channel.send(embed=e_obj)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            e_obj = await em(ctx, title="Error",
                             content=[("Problem","Please enter a numerical Discord ID.")],
                             colour=self.errorColour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)