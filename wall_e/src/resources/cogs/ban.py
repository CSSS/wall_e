import asyncio
import datetime
from typing import Union

import discord
import pytz
from discord.ext import commands

from WalleModels.models import BanRecords
from resources.utilities.embed import embed as em
from resources.utilities.file_uploading import start_file_uploading
from resources.utilities.setup_logger import Loggers

BanAction = discord.AuditLogAction.ban


class Ban(commands.Cog):

    def __init__(self, bot, config, bot_loop_manager):
        log_info = Loggers.get_logger(logger_name="Ban")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.bot = bot
        self.config = config
        self.ban_list = []
        self.error_colour = 0xA6192E
        self.mod_channel = None
        self.guild: discord.Guild = None
        self.bot_loop_manager = bot_loop_manager

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path, "ban_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path, "ban_error"
            )

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        while self.guild is None:
            await asyncio.sleep(2)
        mod_channel_id = await self.bot_loop_manager.create_or_get_channel_id(
            self.logger, self.guild, self.config.get_config_value('basic_config', 'ENVIRONMENT'),
            "ban"
        )
        self.mod_channel = discord.utils.get(
            self.guild.channels, id=mod_channel_id
        )

        # read in ban_list of banned users
        self.logger.info('[Ban load()] loading ban list from the database')
        self.ban_list = await BanRecords.get_all_active_ban_user_ids()
        count = await BanRecords.get_active_bans_count()
        self.logger.info(f"[Ban load()] loaded {count} banned users from database")

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        while self.guild is None:
            await asyncio.sleep(2)
        """Watches for users joining the guild and kicks and bans a user if they are banned"""

        if member.id in self.ban_list:
            self.logger.info(
                f"[Ban watchdog()] banned member, {member}, detected. Promply will notify and kick them."
            )

            e_obj = discord.Embed(title="Ban Notification",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.now(pytz.utc)
                                  )
            e_obj.add_field(name="Notice", value=f"**You are PERMANENTLY BANNED from\n{self.guild}\n\n"
                            "You may NOT rejoin the guild!**")
            e_obj.set_footer(icon_url=self.guild.icon, text=self.guild)

            try:
                await member.send(embed=e_obj)
            except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
                self.logger.info('[Ban watchdog()] unable to send warning dm to banned user due to user dm settings.')
            await member.kick(reason="Not allowed back on server.")

    @commands.Cog.listener(name='on_member_ban')
    async def intercept(self, guild: discord.Guild, member: Union[discord.User, discord.Member]):
        while self.guild is None:
            await asyncio.sleep(2)
        """Watches for a guild ban. The guild ban is undone and the user is banned via this ban system"""

        # need to read the audit log to grab mod, date, and reason
        self.logger.info(f"[Ban intercept()] guild ban detected and intercepted for user='{member}'")
        self.logger.info("[Ban intercept()] waiting 1 second to ensure ban log is created")
        # sleep is needed so discord has time to create the audit log
        await asyncio.sleep(1)

        try:
            def pred(ban: discord.AuditLogEntry):
                return member.id == ban.target.id
            audit_ban = await discord.utils.find(pred, self.guild.audit_logs(action=BanAction, oldest_first=False))
        except Exception as e:
            self.logger.info(f'[Ban intercept()] error while fetching ban data: {e}')
            await self.mod_channel.send(f"Encountered following error while intercepting a ban: {e}\n" +
                                        "**Most likely need view audit log perms.**")
            return

        if audit_ban is None:
            self.logger.info(
                "[Ban intercept()] Problem occurred with ban intercept, aborting and notifying mod channel"
            )
            await self.mod_channel.send(f"Ban for {member.name} has not been added to walle due to error"
                                        "Please use `.convertbans` then `.purgebans` to add to walle system.")
            return

        self.logger.info(f"[Ban intercept()] audit log data retrieved for intercepted ban: {audit_ban}")

        # name, id, mod, mod id, date, reason
        ban = BanRecords(
                         username=member.name + '#' + member.discriminator,
                         user_id=member.id,
                         mod=audit_ban.user.name + '#' + audit_ban.user.discriminator,
                         mod_id=audit_ban.user.id,
                         ban_date=audit_ban.created_at.timestamp(),
                         reason=audit_ban.reason if audit_ban.reason else 'No Reason Given!'
                         )

        # update ban_list and db
        self.ban_list.append(member.id)
        await BanRecords.insert_record(ban)

        # unban
        await guild.unban(member)
        self.logger.info(f"[Ban intercept()] ban for {ban.username} moved into db and guild ban was removed")

        # report to council
        e_obj = discord.Embed(title="Ban Hammer Deployed",
                              colour=discord.Color.red())

        e_obj.add_field(name="Banned User", value=f"**{ban.username}**", inline=True)
        e_obj.add_field(name="Moderator", value=f"**{ban.mod}**", inline=True)
        e_obj.add_field(name="Reason", value=f"```{ban.reason}```", inline=False)
        e_obj.add_field(name="Notification DM", value="*NOT SENT*\nCause: NO COMMON GUILD\n", inline=False)
        e_obj.set_footer(text="Intercepted Moderator Action")
        e_obj.timestamp = audit_ban.created_at
        await self.mod_channel.send(embed=e_obj)
        self.logger.info(
            f"[Ban intercept()] Message sent to mod channel,{self.mod_channel}, for ban of {ban.username}."
        )

    @commands.command()
    async def convertbans(self, ctx):
        """Reads in all guild bans into this ban system"""

        self.logger.info(f"[Ban convertbans()] convertbans command detected from {ctx.author}")

        try:
            # audit logs contains info about user who did the banning, the timestamp of the ban, and the reason
            # however audit logs only go back 3 months, so have to read older bans from the bans list
            ban_logs = {
                ban_log.target.id: ban_log
                for ban_log in [ban async for ban in self.guild.audit_logs(action=BanAction)]
            }
            guild_ban_list = [ban async for ban in self.guild.bans()]
        except Exception as e:
            self.logger.info(f'[Ban convertbans()] error while fetching ban data: {e}')
            await ctx.send(f"Encountered the following errors: {e}\n**Most likely need view audit log perms.**")
            return

        if not guild_ban_list:
            self.logger.info("[Ban convertbans()] No bans to migrate into the ban system from guild. "
                             "Sening message and ending command.")
            await ctx.send("There are no bans to migrate from the guild to the wall_e ban systeme.")
            return

        self.logger.info(f"[Ban convertbans()] retrieved audit log data for ban actions: {ban_logs}")
        self.logger.info(f"[Ban convertbans()] retrieved ban list from guild: {guild_ban_list}")

        self.logger.info("[Ban convertbans()] Starting process to move all guild bans into db")

        # update self.ban_list
        ban_records = []
        for ban in guild_ban_list:
            # NOTE: In the unlikely case there are >1 bans for the same user only 1 will be recorded
            if ban.user.id not in self.ban_list:
                self.ban_list.append(ban.user.id)

                mod = None
                mod_id = None
                ban_date = None
                reason = 'No Reason Given!'

                if ban.user.id in ban_logs:
                    banned = ban_logs[ban.user.id]
                    username = banned.target.name + '#' + banned.target.discriminator
                    user_id = banned.target.id
                    mod = banned.user.name + '#' + banned.user.discriminator
                    mod_id = banned.user.id
                    ban_date = banned.created_at.timestamp()
                    reason = banned.reason if banned.reason else 'No Reason Given!'

                else:
                    username = ban.user.name + '#' + ban.user.discriminator
                    user_id = ban.user.id

                ban_records.append(BanRecords(
                    username=username,
                    user_id=user_id,
                    mod=mod,
                    mod_id=mod_id,
                    ban_date=ban_date,
                    reason=reason
                ))

        await BanRecords.insert_records(ban_records)

        await ctx.send(f"Moved `{len(ban_records)}` active bans from guild bans to walle bans.")
        self.logger.info(f"[Ban convertbans()] total of {len(ban_records)} bans moved into walle ban system")

    @commands.command()
    async def ban(self, ctx, user: discord.Member, *args):

        """Bans a user from the guild"""
        self.logger.info(f"[Ban ban()] Ban command detected from {ctx.author} with args: user={user}, args={args}")

        # confirm at least 1 @ mention of user to ban
        if len(ctx.message.mentions) < 1:
            self.logger.info("[Ban ban()] No user were @ mentioned in the args")
            e_obj = await em(self.logger, ctx=ctx, title="Invalid Arguments",
                             content=[("Error", "Please @ mention the user to ban"),
                                      ("Command Usage", "`.ban @user [<# of days to purge messages>] [<reason>]`"),
                                      ("Example Usage", "`.ban @user1 2 they're being weird`")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        self.logger.info(f"[Ban ban()] User to ban: {user}")

        args = list(args)
        purge_window_days = 1
        try:
            # check if purge window was specified
            purge_window_days = int(args[0])
            args.remove(args[0])
        except Exception:
            # use default value set above
            pass
        self.logger.info(f"[Ban ban()] Purge window days set to {purge_window_days}")

        # construct reason
        reason = ' '.join(args)
        reason = reason if reason else "No Reason Given."
        self.logger.info(f"[Ban ban()] Ban reason '{reason}'")

        # ban
        dm = True

        ban = BanRecords(
                         username=user.name + '#' + user.discriminator,
                         user_id=user.id,
                         mod=ctx.author.name+'#'+ctx.author.discriminator,
                         mod_id=ctx.author.id,
                         reason=reason
                         )

        self.logger.info(f"[Ban ban()] Banning {ban.username} with id {ban.user_id}")

        # add to ban_list
        self.ban_list.append(ban.user_id)

        # dm banned user
        e_obj = discord.Embed(title="Ban Notification",
                              description="You have been **PERMANENTLY BANNED** from " +
                              f"**{self.guild.name.upper()}**",
                              color=discord.Color.red(),
                              timestamp=datetime.datetime.now(pytz.utc)
                              )
        e_obj.add_field(name='Reason',
                        value=f"```{reason}```\n" +
                        "**Please refrain from this kind of behaviour in the future. Thank you.**"
                        )

        e_obj.set_footer(icon_url=self.guild.icon, text=self.guild)
        try:
            await user.send(embed=e_obj)
            self.logger.info("[Ban ban()] User notified via dm of their ban")
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
            dm = False
            self.logger.info("[Ban ban()] Notification dm to user failed due to user preferences")

        # kick
        await user.kick(reason=reason)
        dt = datetime.datetime.now(pytz.utc)
        ban.ban_date = dt.timestamp()

        self.logger.info(f"[Ban ban()] User kicked from guiled at {dt}.")

        # begin purging messages from user in the last purge_window_days
        await self.purge_messages(ctx, user, purge_window_days)

        # report to council
        e_obj = discord.Embed(title="Ban Hammer Deployed",
                              colour=discord.Color.red())

        e_obj.add_field(name="Banned User", value=f"**{ban.username}**", inline=True)
        e_obj.add_field(name="Moderator", value=f"**{ban.mod}**", inline=True)
        e_obj.add_field(name="Reason", value=f"```{ban.reason}```", inline=False)
        e_obj.add_field(name="User Notified via DM", value="*YES*\n" if dm else "*NO*\n*USER HAS DM's DISABLED*",
                        inline=False)
        e_obj.set_footer(text="Moderator Action")
        e_obj.timestamp = dt

        await self.mod_channel.send(embed=e_obj)
        self.logger.info(
            f"[Ban ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {ban.username}."
        )

        # update database
        await BanRecords.insert_record(ban)

    async def purge_messages(self, ctx, user: discord.User, timeframe):
        # first do the ban
        if timeframe <= 0 or timeframe > 14:
            await ctx.send('Window to purge message must be between 1 - 14 days. Using default of `1 day`')
            timeframe = 1
        self.logger.info(f"[Ban purge_messages()] timeframe: {timeframe}")

        # begin purging messages
        # get list of all channels
        channels = self.guild.text_channels

        def is_banned_user(msg):
            return msg.author == user

        date = discord.utils.utcnow() - datetime.timedelta(timeframe)
        self.logger.info(f"[Ban purge_messages()] message from {user} will be purge starting from date {date}")

        for channel in channels:
            send_perm = channel.overwrites_for(ctx.guild.default_role).send_messages
            view_perm = channel.overwrites_for(ctx.guild.default_role).view_channel

            # skip private channels and read-only channels
            # because the user wouldn't have any messages in these channels
            if view_perm is False or send_perm is False:
                continue
            else:
                await channel.purge(limit=100, check=is_banned_user, after=date, bulk=True)

    @commands.command()
    async def unban(self, ctx, user_id: int):
        """Unbans a user"""

        self.logger.info(f"[Ban unban()] unban command detected from {ctx.author} with args=[ {user_id} ]")
        if user_id not in self.ban_list:
            self.logger.info(f"[Ban unban()] Provided id: {user_id}, does not belong to a banned member.")
            e_obj = await em(self.logger, ctx=ctx, title="Error",
                             content=[("Problem",
                                       f"`{user_id}` is either not a valid Discord ID **OR** is not a banned user.")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # "unban"
        self.ban_list.remove(user_id)

        name = await BanRecords.unban_by_id(user_id)
        if not name:
            self.logger.info(f"[Ban unban()] No user with id: {user_id} found.")
            await self.mod_channel.send(f"*No user with id: **{user_id}** found.*")

        self.logger.info(f"[Ban unban()] User: {name} with id: {user_id} was unbanned.")
        e_obj = await em(
            self.logger, ctx=ctx, title="Unban", description=f"**`{name}`** was unbanned.", colour=discord.Color.red()
        )
        if e_obj:
            await self.mod_channel.send(embed=e_obj)

    @unban.error
    async def unban_error(self, ctx, error):
        """Catches an error in unban when a non integer is passed in as an argument"""

        self.logger.info("[Ban unban_error] caught non integer ID passed into unban parameter. Handled accordingly")
        if isinstance(error, commands.BadArgument):
            e_obj = await em(self.logger, ctx=ctx, title="Error",
                             content=[("Problem", "Please enter a numerical Discord ID.")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def bans(self, ctx):
        """Gets all banned users"""

        self.logger.info(f"[Ban bans()] bans command detected from {ctx.author}")

        bans = await BanRecords.get_all_active_bans()
        count = await BanRecords.get_active_bans_count()
        self.logger.info(f"[Ban bans()] retrieved all banned users: {bans}")

        emb = discord.Embed(title="Banned members", color=discord.Color.red())

        names = ""
        ids = ""
        for ban in bans:
            name = ban['username']
            user_id = ban['user_id']
            if len(names) + len(name) > 1024 or (len(ids) + len(str(user_id))) > 1024:
                emb.add_field(name="Names", value=names, inline=True)
                emb.add_field(name="IDs", value=ids, inline=True)
                await ctx.send(embed=emb)
                emb.clear_fields()
                names = ""
                ids = ""

            names += f"{name}\n"
            ids += f"{user_id}\n"

        # send out the last bit, if not empy
        if names:
            emb.add_field(name="Names", value=names, inline=True)
            emb.add_field(name="IDs", value=ids, inline=True)
            await ctx.send(embed=emb)
        await ctx.send(f"Total number of banned users: {count}")
        self.logger.info("[Ban bans()] done sending embeds with banned user lists and total ban count")

    @commands.command()
    async def purgebans(self, ctx):
        """Clears the ban list on the guild."""

        self.logger.info(f"[Ban purgebans()] purgebans command detected from {ctx.author}")

        bans = [ban async for ban in self.guild.bans()]
        self.logger.info(f"[Ban purgebans()] Retrieved list of banned users from guild: {bans}")

        if not bans:
            self.logger.info("[Ban purgebans()] Ban list is empty. Sending message and ending command.")
            await ctx.send("Ban list is empty. Nothing to purge.")
            return

        for ban in bans:
            self.logger.info(f"[Ban purgebans()] Unbanning user: {ban}")
            await self.guild.unban(ban.user)

        await ctx.send(f"**GUILD BAN LIST PURGED**\nTotal # of users unbanned: {len(bans)}")

    def cog_unload(self):
        self.logger.info('[Ban cog_unload()] Removing listeners for ban cog: on_ready, on_member_join, on_member_ban')
        self.bot.remove_listener(self.load, 'on_ready')
        self.bot.remove_listener(self.watchdog, 'on_member_join')
        self.bot.remove_listener(self.intercept, 'on_member_ban')
