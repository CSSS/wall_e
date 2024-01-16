import asyncio
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utilities.autocomplete.banned_users_choices import get_banned_users
from utilities.global_vars import bot, wall_e_config
from utilities.paginate import paginate_embed
from wall_e_models.customFields import pstdatetime

from wall_e_models.models import BanRecord

from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers, print_wall_e_exception

BanAction = discord.AuditLogAction.ban


class Ban(commands.Cog):

    ban_list = {}
    embed_title = f'{bot.user.name} Ban System: '

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Ban")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[Ban __init__()] initializing Ban")
        self.mod_channel = None
        self.guild: discord.Guild = None
        self.purge_messages_task.start()

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "ban_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path, "ban_warn"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "ban_error"
            )

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info('[Ban load()] loading mod_channel and ban_list')
        mod_channel_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            "ban"
        )
        self.mod_channel = discord.utils.get(
            self.guild.channels, id=mod_channel_id
        )

        # read in ban_list of banned users
        self.logger.debug('[Ban load()] loading ban list from the database')
        Ban.ban_list = await BanRecord.get_all_active_ban_user_ids()
        count = await BanRecord.get_active_bans_count()
        self.logger.debug(f"[Ban load()] loaded {count} banned users from database")

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        """Watches for users joining the guild and kicks and bans a user if they are banned"""
        while self.guild is None:
            await asyncio.sleep(2)

        if member.id in Ban.ban_list:
            self.logger.info(
                f"[Ban watchdog()] banned member, {member}, detected. Promply will notify and kick them."
            )
            e_obj = await embed(
                self.logger,
                title=f'{Ban.embed_title} Notification',
                author=bot.user,
                colour=WallEColour.ERROR,
                content=[
                        ("Notice", f"**You are PERMANENTLY BANNED from\n{self.guild}\n\n"
                                   f"You may NOT rejoin the guild!**", False)
                ],
                validation=False,
                channels=self.guild.channels
            )
            if e_obj:
                e_obj.timestamp = pstdatetime.now().pst
                e_obj.set_footer(icon_url=self.guild.icon, text=self.guild)

                try:
                    await member.send(embed=e_obj)
                except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
                    self.logger.debug(
                        '[Ban watchdog()] unable to send warning dm to banned user due to user dm settings.'
                    )
            await member.kick(reason="Not allowed back on server.")

    async def wall_e_ban(self, banned_user, mod, purge_window_days=1, reason="No Reason Given.",
                         ban_date=None, intercepted_moderator_action=False, interaction=None, channels=None):
        """
        Performs the actual ban on the user

        :param banned_user: user that is being banned
        :param mod: moderator who is banning user
        :param purge_window_days: number of days of messages to purge
        :param reason: the reason to ban the user
        :param ban_date: the date that the user is being banned
        :param intercepted_moderator_action: whether the ban is intercepting a discord ban
        :param interaction: the interaction object the function got from the ban slash command
        :return:
        """
        send_function_for_messages = self.mod_channel.send if interaction is None else \
            interaction.edit_original_response
        if banned_user.id in Ban.ban_list:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=bot.user,
                title=f'{Ban.embed_title} Error',
                description=f"{banned_user} already in WALL-E ban system",
                colour=WallEColour.ERROR,
                validation=False,
                channels=channels
            )
            if e_obj:
                await send_function_for_messages(embed=e_obj)
                await asyncio.sleep(5)
            return

        # determine if bot is able to kick the user
        sorted_list_of_banner_user_roles = sorted(banned_user.roles, key=lambda x: int(x.position), reverse=True)
        banned_user_highest_role = sorted_list_of_banner_user_roles[0]
        bot_guild_member = await self.guild.fetch_member(bot.user.id)
        sorted_list_of_bot_roles = sorted(bot_guild_member.roles, key=lambda x: int(x.position), reverse=True)
        bot_highest_role = sorted_list_of_bot_roles[0]
        if banned_user_highest_role > bot_highest_role:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=bot.user,
                title=f'{Ban.embed_title} Error',
                description=f"{banned_user}'s permission is higher than WALL_E so it can't be kicked",
                colour=WallEColour.ERROR,
                validation=False,
                channels=channels
            )
            if e_obj:
                await send_function_for_messages(embed=e_obj)
                await asyncio.sleep(5)
            return

        self.logger.debug(f"[Ban wall_e_ban()] User to ban: {banned_user}")
        self.logger.debug(f"[Ban wall_e_ban()] Ban reason '{reason}'")

        Ban.ban_list[banned_user.id] = banned_user.name
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=bot.user,
            title=f"{Ban.embed_title} Notification",
            description=f"Attempting to ban {banned_user.display_name}({banned_user.name})",
            validation=False,
            channels=channels
        )
        invoked_channel_msg = None
        if e_obj:
            invoked_channel_msg = await send_function_for_messages(embed=e_obj)

        banned_user_dm_able = True

        ban = BanRecord(
            username=banned_user.name + '#' + banned_user.discriminator,
            user_id=banned_user.id,
            mod=mod.name+'#'+mod.discriminator,
            mod_id=mod.id,
            reason=reason,
            ban_date=ban_date.timestamp(),
            purge_window_days=purge_window_days,
            is_purged=False
        )
        await BanRecord.insert_record(ban)

        self.logger.debug(f"[Ban wall_e_ban()] Created BanRecord {ban.username} with id {ban.user_id}")

        # dm banned user
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=bot.user,
            title=f'{Ban.embed_title} Notification',
            description=f"You have been **PERMANENTLY BANNED** from **{self.guild.name.upper()}**",
            colour=WallEColour.ERROR,
            content=[
                ('Reason',
                 f"```{reason}```\n**Please refrain from this kind of behaviour in the future. Thank you.**")
            ],
            validation=False,
            channels=channels
        )
        if e_obj:
            e_obj.timestamp = pstdatetime.now().pst
            e_obj.set_footer(icon_url=self.guild.icon, text=self.guild)

            try:
                await banned_user.send(embed=e_obj)
                self.logger.debug("[Ban wall_e_ban()] User notified via dm of their ban")
            except (discord.HTTPException, discord.Forbidden, discord.errors.Forbidden):
                banned_user_dm_able = False
                self.logger.debug("[Ban wall_e_ban()] Notification dm to user failed due to user preferences")

        # kick
        await banned_user.kick(reason=reason)
        self.logger.debug(f"[Ban wall_e_ban()] User kicked from guild at {ban_date}.")

        # report to council
        e_obj = await embed(
            self.logger,
            interaction=interaction,
            author=bot.user,
            title=f'{Ban.embed_title} Hammer Deployed',
            colour=WallEColour.ERROR,
            content=[
                ("Banned User", f"**{ban.username}**"),
                ("Moderator", f"**{ban.mod}**",),
                ("Reason", f"```{ban.reason}```", False),
                (
                    "User Notified via DM",
                    "*YES*\n" if banned_user_dm_able else "*NO*\n*USER HAS DM's DISABLED or NO COMMON GUILD*",
                    False
                ),
                ("Days of Messages to Purge", f"{purge_window_days}"),
                ("Purge Complete", "False")
            ],
            footer="Intercepted Moderator Action" if intercepted_moderator_action else "Moderator Action",
            validation=False,
            channels=channels
        )
        if e_obj:
            e_obj.timestamp = ban_date
            await asyncio.sleep(5)
            if invoked_channel_msg:
                await invoked_channel_msg.delete()
            await self.mod_channel.send(embed=e_obj)
            self.logger.debug(
                f"[Ban wall_e_ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {ban.username}."
            )

    @commands.Cog.listener(name='on_member_ban')
    async def intercept(self, guild: discord.Guild, member: Union[discord.User, discord.Member]):
        """Watches for a guild ban. The guild ban is undone and the user is banned via this ban system"""
        while self.guild is None:
            await asyncio.sleep(2)
        if member.id in Ban.ban_list:
            e_obj = await embed(
                self.logger,
                author=bot.user,
                title=f'{Ban.embed_title} Guild Ban Intercept',
                colour=WallEColour.ERROR,
                description=f"Not converting guild ban for {member} to wall_e ban as user is already wall_e banned",
                validation=False,
                channels=guild.channels
            )
            if e_obj:
                await self.mod_channel.send(embed=e_obj)
            return
        e_obj = await embed(
            self.logger,
            author=bot.user,
            title=f'{Ban.embed_title} Guild Ban Intercept',
            colour=WallEColour.ERROR,
            description=f"Attempting to convert Guild ban for {member} into a {bot.user.name} ban",
            validation=False,
            channels=guild.channels
        )
        if not e_obj:
            return
        msg = await self.mod_channel.send(embed=e_obj)
        # need to read the audit log to grab mod, date, and reason
        self.logger.info(f"[Ban intercept()] guild ban detected and intercepted for user='{member}'")
        # sleep is needed so discord has time to create the audit log
        await asyncio.sleep(1)

        try:
            def get_audit_log(ban: discord.AuditLogEntry):
                return member.id == ban.target.id
            audit_ban = await discord.utils.find(
                get_audit_log, self.guild.audit_logs(action=BanAction, oldest_first=False)
            )
        except Exception as e:
            error_message = (f"Encountered following error while intercepting a ban for {member}: \n{e}\n"
                             f"**Most likely need view audit log perms.**")
            self.logger.warn(f'[Ban intercept()] {error_message}')
            e_obj = await embed(
                self.logger,
                author=bot.user,
                title=f'{Ban.embed_title} Guild Ban Intercept',
                colour=WallEColour.ERROR,
                description=error_message,
                validation=False,
                channels=guild.channels
            )
            if e_obj:
                await msg.edit(embed=e_obj)
            return

        if audit_ban is None:
            self.logger.warn(
                "[Ban intercept()] Problem occurred with ban intercept, aborting and notifying mod channel"
            )
            e_obj = await embed(
                self.logger,
                author=bot.user,
                title=f'{Ban.embed_title} Guild Ban Intercept',
                colour=WallEColour.ERROR,
                description=(
                    f"Unable to get guild ban for {member} to convert to wall_e ban. "
                    f"Please use `.convertbans` then `.purgebans` to try and manually convert ban."
                ),
                validation=False,
                channels=guild.channels
            )
            if e_obj:
                await msg.edit(embed=e_obj)
            return

        self.logger.debug(f"[Ban intercept()] audit log data retrieved for intercepted ban: {audit_ban}")
        reason = audit_ban.reason if audit_ban.reason else 'No Reasons Given.'
        await self.wall_e_ban(
            member, audit_ban.user, reason=reason, ban_date=audit_ban.created_at,
            intercepted_moderator_action=True, channels=guild.channels
        )

        await guild.unban(member)
        self.logger.debug(f"[Ban intercept()] ban for {member} moved into db and guild ban was removed")

        e_obj = await embed(
            self.logger,
            author=bot.user,
            title=f'{Ban.embed_title} Guild Ban Intercept',
            colour=WallEColour.ERROR,
            description=f"{member}'s ban successfully converted to a {bot.user.name} ban",
            validation=False,
            channels=guild.channels
        )
        if e_obj:
            await msg.edit(embed=e_obj)
        self.logger.debug(
            f"[Ban intercept()] Message sent to mod channel [{self.mod_channel}] for ban of [{member}]."
        )

    @commands.command(
        brief="Reads in all guild bans into this ban system",
        help=(
            "Command will read in all the guild bans into wall_e database to use custom ban system.\n"
            "**Can only be used ONCE.**"
        )
    )
    @commands.has_any_role("Minions", "Moderator")
    async def convertbans(self, ctx):
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
            self.logger.debug(f'[Ban convertbans()] error while fetching ban data: {e}')
            e_obj = await embed(
                self.logger,
                author=bot.user,
                title=f'{Ban.embed_title} convertbans',
                colour=WallEColour.ERROR,
                description=f"Encountered the following errors: {e}\n**Most likely need view audit log perms.**"
            )
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        if not guild_ban_list:
            self.logger.debug("[Ban convertbans()] No bans to migrate into the ban system from guild. "
                              "Sening message and ending command.")
            await ctx.send(
                "There are no bans to migrate from the guild to the wall_e ban system.", reference=ctx.message
            )
            return

        self.logger.debug(f"[Ban convertbans()] retrieved audit log data for ban actions: {ban_logs}")
        self.logger.debug(f"[Ban convertbans()] retrieved ban list from guild: {guild_ban_list}")

        self.logger.debug("[Ban convertbans()] Starting process to move all guild bans into db")

        # update Ban.ban_list
        ban_records = []
        for ban in guild_ban_list:
            # NOTE: In the unlikely case there are >1 bans for the same user only 1 will be recorded
            if ban.user.id not in Ban.ban_list:
                Ban.ban_list[ban.user.id] = ban.user.name

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
                    ban_date = banned.created_at
                    reason = banned.reason if banned.reason else 'No Reason Given!'

                else:
                    username = ban.user.name + '#' + ban.user.discriminator
                    user_id = ban.user.id

                ban_records.append(BanRecord(
                    username=username,
                    user_id=user_id,
                    mod=mod,
                    mod_id=mod_id,
                    ban_date=ban_date,
                    reason=reason
                ))

        await BanRecord.insert_records(ban_records)

        e_obj = await embed(
            self.logger,
            author=bot.user,
            title=f'{Ban.embed_title} convertbans',
            description=f"Moved `{len(ban_records)}` active bans from guild bans to wall_e bans."
        )
        if e_obj:
            await ctx.send(embed=e_obj)
        self.logger.debug(f"[Ban convertbans()] total of {len(ban_records)} bans moved into wall_e ban system")

    @app_commands.command(name="ban", description="Bans a user from the guild")
    @app_commands.describe(user="user to unban")
    @app_commands.checks.has_any_role("Minions", "Moderator")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, purge_window_days: int = 1,
                  reason: str = "No Reason Given."):
        self.logger.info(
            f"[Ban ban()] Ban command detected from {interaction.user} with args: user={user}, "
            f"purge_window_days={purge_window_days}, reason={reason}"
        )
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            await interaction.channel.send(
                "Feeling a bit overloaded at the moment...Please try again in a few minutes"
            )
            return
        if purge_window_days <= 0 or purge_window_days > 14:
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Invalid Purge Specified',
                description=f'Window to purge message must be between 1 - 14 days instead of {purge_window_days}. '
                            f'Using default of `1 day`'
            )
            if e_obj:
                await interaction.followup.send(embed=e_obj)
                await asyncio.sleep(5)
            purge_window_days = 1
        self.logger.debug(f"[Ban ban()] Purge window days set to {purge_window_days}")

        self.logger.debug(f"[Ban ban()] Ban reason '{reason}'")
        await self.wall_e_ban(
            interaction.namespace.user, interaction.user, purge_window_days=purge_window_days, reason=reason,
            ban_date=pstdatetime.now(), interaction=interaction
        )
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    @app_commands.command(name="unban", description="Unbans the specified user")
    @app_commands.describe(user_id="user to unban")
    @app_commands.autocomplete(user_id=get_banned_users)
    @app_commands.checks.has_any_role("Minions", "Moderator")
    async def unban(self, interaction: discord.Interaction, user_id: str):
        self.logger.info(f"[Ban unban()] unban command detected from {interaction.user} with args=[ {user_id} ]")
        if user_id == "-1" or not user_id.isdigit():
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description="Invalid input detected. Please try again.",
                colour=WallEColour.ERROR,
                title=f'{Ban.embed_title} Unban Error'
            )
            if e_obj:
                await interaction.response.send_message(embed=e_obj)
                await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            await interaction.channel.send(
                "Feeling a bit overloaded at the moment...Please try again in a few minutes"
            )
            return
        user_id = int(user_id)
        if user_id not in Ban.ban_list:
            self.logger.debug(f"[Ban unban()] Provided id: {user_id}, does not belong to a banned member.")
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Error',
                content=[
                    ("Problem",
                     f"`{user_id}` is either not a valid Discord ID **OR** is not a banned user.")
                ],
                colour=WallEColour.ERROR,
                footer="Command Error"
            )
            if e_obj:
                await interaction.followup.send(embed=e_obj)
            return

        del Ban.ban_list[user_id]

        name = await BanRecord.unban_by_id(user_id)
        if name:
            self.logger.debug(f"[Ban unban()] User: {name} with id: {user_id} was unbanned.")
            mod_channel_e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Unbanned',
                content=[('Unbanned User', name), ("Moderator", interaction.user.name)]
            )
            if mod_channel_e_obj:
                await self.mod_channel.send(embed=mod_channel_e_obj)
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Notification',
                description=f"**`{name}`** has been unbanned."
            )
        else:
            self.logger.debug(f"[Ban unban()] No user with id: {user_id} found.")
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Error',
                description=f"**`{name}`** was not banned.",
                colour=WallEColour.ERROR
            )

        if e_obj:
            await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(10)
            await interaction.delete_original_response()

    @app_commands.command(name="bans", description="Gets all banned users")
    @app_commands.describe(search_query="username to search for")
    @app_commands.checks.has_any_role("Bot_manager", "Minions", "Moderator")
    @app_commands.autocomplete(search_query=get_banned_users)
    async def bans(self, interaction: discord.Interaction, search_query: str = None):
        self.logger.info(f"[Ban bans()] bans command detected from {interaction.user}")
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            await interaction.channel.send(
                "Feeling a bit overloaded at the moment...Please try again in a few minutes"
            )
            return

        bans = await BanRecord.get_all_active_bans(search_query)
        self.logger.debug(f"[Ban bans()] retrieved all banned users: {bans}")

        names = ""
        user_ids = ""
        ban_dates = ""
        content_to_embed = []
        number_of_members_per_page = 20
        number_of_members = 0
        for ban in bans:
            name = ban['username']
            user_id = ban['user_id']
            ban_date = ban['ban_date']
            names += f"\n{name}"
            user_ids += f"\n{user_id}"
            ban_dates += f'\n{ban_date.pst.strftime("%Y-%m-%d %I:%M:%S %p")}' if ban_date else f"\n{ban_date}"
            number_of_members += 1
            if number_of_members % number_of_members_per_page == 0 or number_of_members == len(bans):
                number_of_members = 0
                content_to_embed.append(
                    [["Names", names], ["User IDs", user_ids], ["Ban Date [PST]", ban_dates]]
                )
                names = ""
                user_ids = ""
                ban_dates = ""
        if len(content_to_embed) == 0:
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{Ban.embed_title} Error',
                description=f"Could not find a banned user whose username contains `{search_query}`",
                colour=WallEColour.ERROR
            )
            if e_obj:
                msg = await interaction.followup.send(embed=e_obj)
                await asyncio.sleep(10)
                await msg.delete()
        else:
            await paginate_embed(
                self.logger, bot, content_to_embed=content_to_embed,
                title=f"{Ban.embed_title} {len(bans)} Banned members",
                interaction=interaction
            )

        self.logger.debug("[Ban bans()] done sending embeds with banned user lists and total ban count")

    @app_commands.command(name="purgebans", description="Clears the ban list on the guild.")
    @app_commands.checks.has_any_role("Minions", "Moderator")
    async def purgebans(self, interaction: discord.Interaction):
        self.logger.info(f"[Ban purgebans()] purgebans command detected from {interaction.user}")
        await interaction.response.defer()

        bans = [ban async for ban in self.guild.bans()]
        self.logger.debug(f"[Ban purgebans()] Retrieved list of banned users from guild: {bans}")

        if not bans:
            self.logger.debug("[Ban purgebans()] Ban list is empty. Sending message and ending command.")
            e_obj = await embed(
                self.logger, interaction=interaction, title=f'{bot.user.name} Ban',
                description="Ban list is empty. Nothing to purge.",
            )
            if e_obj:
                msg = await interaction.followup.send(e_obj)
                await asyncio.sleep(10)
                await msg.delete()
            return

        for ban in bans:
            self.logger.debug(f"[Ban purgebans()] Unbanning user: {ban}")
            await self.guild.unban(ban.user)

        e_obj = await embed(
            self.logger, interaction=interaction, title=f'{Ban.embed_title} Ban',
            description=f"**GUILD BAN LIST PURGED**\nTotal # of users unbanned: {len(bans)}",
        )
        if e_obj:
            msg = await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(10)
            await msg.delete()

    @tasks.loop(seconds=20)
    async def purge_messages_task(self):
        """
        Background function that determines if a reminder's time has come to be sent to its channel
        :return:
        """
        if not self.guild:
            return
        try:
            un_purged_ban_records = await BanRecord.get_unpurged_users()
            number_of_purges = len(un_purged_ban_records)
            msg = None
            for indx, un_purged_ban_record in enumerate(un_purged_ban_records):
                timeframe = un_purged_ban_record.purge_window_days
                self.logger.debug(f"[Ban purge_messages()] timeframe: {timeframe}")

                # begin purging messages
                # get list of all channels
                channels = self.guild.text_channels

                def is_banned_user(msg):
                    return msg.author == un_purged_ban_record.user_id
                import datetime
                date = discord.utils.utcnow() - datetime.timedelta(timeframe)
                self.logger.debug(f"[Ban purge_messages()] message from {un_purged_ban_record.user_id} "
                                  f"will be purge starting from date {date}")
                e_obj = await embed(
                    self.logger, title=f'{Ban.embed_title} [{indx+1}/{number_of_purges}] Purging in Progress',
                    description=(
                        f"Currently purging user {un_purged_ban_record.username}({un_purged_ban_record.user_id}) "
                        f"with a purge day frame of {timeframe}"
                    ), validation=False
                )
                if e_obj:
                    if msg:
                        await msg.delete()
                    msg = await self.mod_channel.send(embed=e_obj)
                    for channel in channels:
                        send_perm = channel.overwrites_for(self.guild.default_role).send_messages
                        view_perm = channel.overwrites_for(self.guild.default_role).view_channel

                        # skip private channels and read-only channels
                        # because the user wouldn't have any messages in these channels
                        if not (view_perm is False or send_perm is False):
                            await channel.purge(limit=100, check=is_banned_user, after=date, bulk=True)
                    await BanRecord.marked_user_as_purged(un_purged_ban_record.ban_id)
            if number_of_purges > 0:
                e_obj = await embed(
                    self.logger, title=f'{Ban.embed_title} Purge Complete',
                    description=f"Succesfully purged {number_of_purges} users", validation=False
                )
                if e_obj:
                    if msg:
                        await msg.delete()
                    await self.mod_channel.send(embed=e_obj)

        except Exception as error:
            self.logger.error('[Reminders get_messages()] Ignoring exception when generating reminder:')
            print_wall_e_exception(error, error.__traceback__, error_logger=self.logger.error)

    def cog_unload(self):
        self.logger.info('[Ban cog_unload()] Removing listeners for ban cog: on_ready, on_member_join, on_member_ban')
        bot.remove_listener(self.load, 'on_ready')
        bot.remove_listener(self.watchdog, 'on_member_join')
        bot.remove_listener(self.intercept, 'on_member_ban')


async def setup(bot):
    await bot.add_cog(Ban())
