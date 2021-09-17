from os import name
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

    async def insert_ban(self, username, user_id):
        query="INSERT INTO Banned_users VAlUES (%s, %s)"
        logger.info(f"[Ban insert_ban()] sql_query=[{query}] with values ({username, user_id})")
        try:
            self.curs.execute(query, (username, user_id))
        except Exception as e:
            logger.info(f'[Ban insert_ban()] sql error: {e}')

    async def insert_record(self, username, user_id, mod, mod_id, date, reason):
        query = "INSERT INTO Ban_records (username, user_id, mod, mod_id, date, reason) " \
              "VALUES (%s, %s, %s, %s, %s, %s)"

        logger.info(f"[Ban insert_record()] sql_query=[{query}] with values " \
                     f"({username, user_id, mod, mod_id, date, reason})")
        try:
            self.curs.execute(query, (username, user_id, mod, mod_id, date, reason))
        except Exception as e:
            logger.info(f'[Ban insert_record()] sql error {e}')

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name="council-summary")

        # read in blacklist of banned users
        try:
            query="SELECT user_id FROM Banned_users;"
            logger.info(f"[Ban load()] sql_query=[ {query} ]")
            self.curs.execute(query)
        except Exception as e:
            logger.info(f"[Ban load()] sql exception: {e}")

        bans = self.curs.fetchall()
        logger.info(f"[Ban load()] loaded the following banned users: {bans}")
        self.blacklist = [int(ban[0]) for ban in bans]

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        if member.id in self.blacklist:
            logger.info(f"[Ban watchdog()] banned member, {member}, detected. Promply will notify and kick them.")

            e_obj = discord.Embed(title="Ban Notification",
                                  color=discord.Color.red(),
                                  timestamp=self.datetime.now(pytz.timezone('Canada/Pacific'))
                                  )
            e_obj.add_field(name="Notice", value=f"**You are PERMANENTLY BANNED from\n{self.bot.guilds[0]}\n\n" +
                                                  "You may NOT rejoin the guild!**")
            e_obj.set_footer(icon_url=self.bot.guilds[0].icon_url, text=self.bot.guilds[0])

            await member.send(embed=e_obj)
            await member.kick(reason="Not allowed back on server.")

    @commands.Cog.listener(name='on_member_ban')
    async def intercept(self, guild: discord.Guild, member: Union[discord.User, discord.Member]):
        # need to read the audit log to grab mod, date, and reason
        logger.info(f"[Ban intercept()] guild ban detected and intercepted for user='{member}'")
        try:
            audit_ban = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
        except Exception as e:
            logger.info(f'error while fetching ban data: {e}')
            await self.mod_channel(f"Encountered following error while intercepting a ban: {e}\n" +
                                   "**Most likely need view audit log perms.**")
            return
        audit_ban = audit_ban[0]
        logger.info(f"[Ban intercept()] audit log data retrieved for intercepted ban: {audit_ban}")

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
        logger.info(f"[Ban intercept()] ban for {username} moved into db and guild ban was removed")

        # report to council
        e_obj = discord.Embed(title="Ban Hammer Deployed",
                                colour=discord.Color.red())

        e_obj.add_field(name="Banned User", value=f"**{username}**", inline=True)
        e_obj.add_field(name="Moderator", value=f"**{mod}**", inline=True)
        e_obj.add_field(name="Reason", value=f"```{reason}```", inline=False)
        e_obj.add_field(name="Notification DM", value="NOT SENT, DUE TO NO COMMON GUILD\n", inline=False)
        e_obj.set_footer(text="Intercepted Moderator Action")

        if e_obj:
            e_obj.timestamp = date.astimezone(pytz.timezone('Canada/Pacific'))
            await self.mod_channel.send(embed=e_obj)
        logger.info(f"[Ban ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {username}.")

    @commands.command()
    async def initban(self, ctx):
        logger.info(f"[Ban initban()] Initban command detected from {ctx.author}")

        try:
            audit_logs = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
            bans = await self.bot.guilds[0].bans()
        except Exception as e:
            logger.info(f'[Ban initban()] error while fetching ban data: {e}')
            await ctx.send(f"Encountered the following sql errors: {e}\n**Most likely need view audit log perms.**")
            return

        logger.info(f"[Ban initban()] retrieved audit log data for ban actions: {audit_logs}")
        logger.info(f"[Ban initban()] retrieved ban list from guild: {bans}")

        logger.info("[Ban initban()] Starting process to move all guild bans into db")
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
        await ctx.send(f"{len(ban_data)} moved from guild bans to db.")
        logger.info(f"[Ban initban()] total of {len(ban_data)} bans moved into db")

    @commands.command()
    async def ban(self, ctx, *args):
        logger.info(f"[Ban ban()] Ban command detected from {ctx.author} with args=[ {args} ]")
        args = list(args)
        mod_info = [ctx.author.name+'#'+ctx.author.discriminator, ctx.author.id]

        # confirm at least 1 @ mention of user to ban
        if len(ctx.message.mentions) < 1:
            logger.info("[Ban ban()] No users were @ mentioned in the args")
            e_obj = await em(ctx=ctx, title="Invalid Arguments",
                             content=[("Error", "Please @ mention the user(s) to ban")],
                             colour=self.errorColour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # get mentions
        users_to_ban = ctx.message.mentions
        logger.info(f"[Ban ban()] list of user to be banned={users_to_ban}")

        # construct reason, but first remove @'s from the args
        reason = ''.join([i+' ' for i in args if not re.match(r'<@!?[0-9]*>', i)])
        reason = reason if reason else "No Reason Given!"
        logger.info(f"[Ban ban()] reason for ban(s)={reason}")

        # ban
        dm = True
        for user in users_to_ban:
            username = user.name + '#' + user.discriminator
            logger.info(f"[Ban ban()] Banning {username} with id {user.id}")

            # add to blacklist
            self.blacklist.append( user.id )

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
                    logger.info("[Ban ban()] User notified via dm of their ban")
            except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
                dm = False
                logger.info("[Ban ban()] Notification dm to user failed due to user preferences")

            # kick
            await user.kick(reason=reason)
            dt = self.datetime.now(pytz.utc)
            logger.info(f"[Ban ban()] User kicked from guiled at {dt}.")

            # report to council
            e_obj = discord.Embed(title="Ban Hammer Deployed",
                                  colour=discord.Color.red())

            e_obj.add_field(name="Banned User", value=f"**{username}**", inline=True)
            e_obj.add_field(name="Moderator", value=f"**{mod_info[0]}**", inline=True)
            e_obj.add_field(name="Reason", value=f"```{reason}```", inline=False)
            e_obj.add_field(name="Notification DM", value="SENT\n" if dm else "NOT SENT, DUE TO USER DM PREF's\n",
                            inline=False)
            e_obj.set_footer(text="Moderator Action")
            if e_obj:
                e_obj.timestamp = dt.astimezone(pytz.timezone('Canada/Pacific'))
                await self.mod_channel.send(embed=e_obj)
            logger.info(f"[Ban ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {username}.")

            # update db
            await self.insert_ban(username, user.id)
            await self.insert_record(username, user.id, mod_info[0], mod_info[1], dt, reason)

    @commands.command()
    async def unban(self, ctx, _id: int):
        logger.info(f"[Ban unban()] unban command detected from {ctx.author} with args=[ {_id} ]")
        if _id not in self.blacklist:
            logger.info(f"Provided id: {_id}, does not belong to a banned member.")
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
            query="SELECT username FROM Banned_users WHERE user_id='%s';"
            logger.info(f"[Ban unban()] sql_query=[{query}] with values ({_id})")

            self.curs.execute(query, [_id])
            name = self.curs.fetchone()[0]

            query="DELETE FROM Banned_users WHERE user_id='%s';"
            logger.info(f"[Ban unban()] sql_query=[{query}] with values ({_id})")
            self.curs.execute(query, [_id])
        except Exception as e:
            logger.info(f'[Ban unban()] Encountered hte following sql error: {e}')
            await ctx.send(f"Encountered the following sql error: {e}")
            return

        logger.info(f"[Ban unban()] User: {name} with id: {_id} was unbanned.")
        e_obj = await em(ctx, title="Unban", description=f"**`{name}`** was unbanned.", colour=discord.Color.red())
        if e_obj:
            await self.mod_channel.send(embed=e_obj)

    @unban.error
    async def unban_error(self, ctx, error):
        logger.info("[Ban Unban_error] caught non integer ID passed into unban parameter. Handled accordingly")
        if isinstance(error, commands.BadArgument):
            e_obj = await em(ctx, title="Error",
                             content=[("Problem","Please enter a numerical Discord ID.")],
                             colour=self.errorColour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def bans(self, ctx):
        logger.info(f"[Ban bans()] bans command detected from {ctx.author}")
        query="SELECT * FROM banned_users;"
        try:
            logger.info(f"sql_query=[{query}]")
            self.curs.execute(query)
        except Exception as e:
            logger.info(f"[Ban bans()] Encountered following sql error: {e}")
            await ctx.send(f"Encountered the following sql error: {e}")
            return

        rows = self.curs.fetchall()
        logger.info(f"[Ban bans()] retrieved all banned users: {rows}")

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
        logger.info("[Ban bans()] done sending embeds with banned user lists")