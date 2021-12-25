from discord.ext import commands
import discord
from resources.utilities.embed import embed as em
from WalleModels.models import BannedUsers, BanRecords
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
        self.ban_list = []
        self.error_colour = 0xA6192E
        self.mod_channel = None

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        """Grabs channel to send mod reports to and reads in the ban_list from db"""

        mod_channel_name = self.config.get_config_value('basic_config', 'MOD_CHANNEL')
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'PRODUCTION':
            await self.make_mod_channel()
        else:
            logger.info(f'[Ban load()] Attempting to get the report channel: {mod_channel_name}')

            self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name=mod_channel_name)
            if self.mod_channel:
                logger.info(f"[Ban load()] #{mod_channel_name} channel successfully found: {self.mod_channel}")
            else:
                logger.info(f"[Ban load()] Couldn't get {mod_channel_name} from guild."
                            " Channel doesn't exist. Exiting.")
                exit('No mod channel')

        # read in ban_list of banned users
        logger.info('[Ban load()] loading ban list from the database')
        self.ban_list = await BannedUsers.get_banned_ids()
        logger.info(f"[Ban load()] loaded the following banned users: {self.ban_list}")

    async def make_mod_channel(self):
        """When ENVIRONMENT is TEST or LOCALHOST: Attempts to get channel for mod report.
        If it doesn't exist attempts to create it, and if that fails then it exits"""

        env = self.config.get_config_value('basic_config', 'ENVIRONMENT')

        if env == 'TEST':
            branch = self.config.get_config_value('basic_config', 'BRANCH_NAME')
            channel_name = f"{branch}_mod_channel"
        elif env == 'LOCALHOST':
            channel_name = self.config.get_config_value('basic_config', 'MOD_CHANNEL')

        logger.info(f"[Ban make_mod_channel()] mod channel is =[{channel_name}]")
        self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name=channel_name.lower())

        if self.mod_channel is None:
            self.mod_channel = await self.bot.guilds[0].create_text_channel(channel_name)

            mod_channel_id = self.mod_channel.id
            if mod_channel_id is None:
                logger.info(
                    f"[Ban make_mod_channel()] the channel designated for mod reports [{channel_name}] "
                    f"in {branch if env == 'TEST' else env +' server'} does not exist and I was unable to create it, "
                    "exiting now...."
                )
                exit(1)
            logger.info(f"[Ban make_mod_channel()] mod channel successfully created [{self.mod_channel}]")
            await self.mod_channel.send('this is a public channel, set to private as you see fit to match prod.')

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        """Watches for users joining the guild and kicks and bans a user if they are banned"""

        if member.id in self.ban_list:
            logger.info(f"[Ban watchdog()] banned member, {member}, detected. Promply will notify and kick them.")

            e_obj = discord.Embed(title="Ban Notification",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.now(pytz.utc)
                                  )
            e_obj.add_field(name="Notice", value=f"**You are PERMANENTLY BANNED from\n{self.bot.guilds[0]}\n\n"
                            "You may NOT rejoin the guild!**")
            e_obj.set_footer(icon_url=self.bot.guilds[0].icon_url, text=self.bot.guilds[0])

            await member.send(embed=e_obj)
            await member.kick(reason="Not allowed back on server.")

    @commands.Cog.listener(name='on_member_ban')
    async def intercept(self, guild: discord.Guild, member: Union[discord.User, discord.Member]):
        """Watches for a guild ban. The guild ban is undone and the user is banned via this ban system"""

        # need to read the audit log to grab mod, date, and reason
        logger.info(f"[Ban intercept()] guild ban detected and intercepted for user='{member}'")
        try:
            audit_ban = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
        except Exception as e:
            logger.info(f'error while fetching ban data: {e}')
            await self.mod_channel.send(f"Encountered following error while intercepting a ban: {e}\n" +
                                        "**Most likely need view audit log perms.**")
            return
        audit_ban = audit_ban[0]
        logger.info(f"[Ban intercept()] audit log data retrieved for intercepted ban: {audit_ban}")

        # name, id, mod, mod id, date, reason
        ban = BannedUsers(
                          username=member.name + '#' + member.discriminator,
                          user_id=str(member.id)
                          )

        record = BanRecords(
                            username=ban.username,
                            user_id=ban.user_id,
                            mod=audit_ban.user.name + '#' + audit_ban.user.discriminator,
                            mod_id=str(audit_ban.user.id),
                            date=audit_ban.created_at.timestamp(),
                            reason=audit_ban.reason if audit_ban.reason else 'No Reason Given!'
                            )

        # update ban_list and db
        self.ban_list.append(ban.user_id)
        await BannedUsers.insert_ban(ban)
        await BanRecords.insert_record(record)

        # unban
        await self.bot.guilds[0].unban(member)
        logger.info(f"[Ban intercept()] ban for {ban.username} moved into db and guild ban was removed")

        # report to council
        e_obj = discord.Embed(title="Ban Hammer Deployed",
                              colour=discord.Color.red())

        e_obj.add_field(name="Banned User", value=f"**{ban.username}**", inline=True)
        e_obj.add_field(name="Moderator", value=f"**{record.mod}**", inline=True)
        e_obj.add_field(name="Reason", value=f"```{record.reason}```", inline=False)
        e_obj.add_field(name="Notification DM", value="*NOT SENT*\nDUE TO NO COMMON GUILD\n", inline=False)
        e_obj.set_footer(text="Intercepted Moderator Action")

        if e_obj:
            e_obj.timestamp = record.date
            await self.mod_channel.send(embed=e_obj)
        logger.info(f"[Ban ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {ban.username}.")

    @commands.command()
    async def convertbans(self, ctx):
        """Reads in all guild bans into this ban system"""

        logger.info(f"[Ban convertbans()] convertbans command detected from {ctx.author}")

        try:
            # audit logs contains info about user who did the banning, the timestamp of the ban, and the reason
            # however audit logs only go back 3 months, so have to read older bans from the bans list
            ban_logs = await self.bot.guilds[0].audit_logs(action=discord.AuditLogAction.ban).flatten()
            guild_ban_list = await self.bot.guilds[0].bans()
        except Exception as e:
            logger.info(f'[Ban convertbans()] error while fetching ban data: {e}')
            await ctx.send(f"Encountered the following errors: {e}\n**Most likely need view audit log perms.**")
            return

        if not guild_ban_list:
            logger.info("[Ban convertbans()] No bans to migrate into the ban system from guild. "
                        "Sening message and ending command."
                        )
            await ctx.send("There are no bans to migrate from the guild to the wall_e ban systeme.")
            return

        logger.info(f"[Ban convertbans()] retrieved audit log data for ban actions: {ban_logs}")
        logger.info(f"[Ban convertbans()] retrieved ban list from guild: {guild_ban_list}")

        logger.info("[Ban convertbans()] Starting process to move all guild bans into db")

        # update self.ban_list
        self.ban_list.extend([ban.user.id for ban in guild_ban_list])
        ban_records = []
        banned_users = []
        ban_log_ids = []
        for ban in ban_logs:
            ban_log_ids.append(ban.target.id)

            ban_records.append(BanRecords(
                                username=ban.target.name+'#'+ban.target.discriminator,
                                user_id=str(ban.target.id),
                                mod=ban.user.name+'#'+ban.user.discriminator,
                                mod_id=str(ban.user.id),
                                date=ban.created_at.timestamp(),
                                reason=ban.reason if ban.reason else 'No Reason Given!'
                                ))

        for ban in guild_ban_list:
            # make BannedUser objects
            banned_users.append(BannedUsers(
                                username=ban.user.name,
                                user_id=str(ban.user.id)
                                ))

            if ban.user.id not in ban_log_ids:
                ban_records.append(BanRecords(
                                   username=ban.user.name+'#'+ban.user.discriminator,
                                   user_id=str(ban.user.id),
                                   mod=None,
                                   mod_id=None,
                                   date=None,
                                   reason='No Reason Given!'
                                   ))

        await BanRecords.insert_records(ban_records)
        await BannedUsers.insert_bans(banned_users)

        await ctx.send(f"Moved `{len(banned_users)}` active bans from guild bans to walle bans.\n" +
                       f"Created `{len(ban_records)}` ban records.")
        logger.info(f"[Ban convertbans()] total of {len(banned_users)} bans and {len(ban_records)} records " +
                    "moved into walle ban system")

    @commands.command()
    async def ban(self, ctx, *args):
        """Bans a user from the guild"""

        logger.info(f"[Ban ban()] Ban command detected from {ctx.author} with args=[ {args} ]")
        args = list(args)
        ban_record = BanRecords(
                                mod=ctx.author.name+'#'+ctx.author.discriminator,
                                mod_id=str(ctx.author.id)
                                )

        # confirm at least 1 @ mention of user to ban
        if len(ctx.message.mentions) < 1:
            logger.info("[Ban ban()] No users were @ mentioned in the args")
            e_obj = await em(ctx=ctx, title="Invalid Arguments",
                             content=[("Error", "Please @ mention the user(s) to ban")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # get mentions
        users_to_ban = ctx.message.mentions
        logger.info(f"[Ban ban()] list of user to be banned={users_to_ban}")

        # construct reason, but first remove @'s from the args
        reason = ' '.join([arg for arg in args if not re.match(r'<@!?[0-9]*>', arg)])
        reason = reason if reason else "No Reason Given!"
        logger.info(f"[Ban ban()] reason for ban(s)={reason}")

        # ban
        dm = True
        bans = []
        records = []
        for user in users_to_ban:
            ban = BannedUsers(
                              username=user.name + '#' + user.discriminator,
                              user_id=str(user.id)
                              )

            record = BanRecords(
                                username=ban.username,
                                user_id=ban.user_id,
                                mod=ban_record.mod,
                                mod_id=ban_record.mod_id,
                                reason=reason
                                )

            logger.info(f"[Ban ban()] Banning {ban.username} with id {ban.user_id}")

            # add to ban_list
            self.ban_list.append(ban.user_id)

            # dm banned user
            e_obj = discord.Embed(title="Ban Notification",
                                  description="You have been **PERMANENTLY BANNED** from " +
                                  f"**{self.bot.guilds[0].name.upper()}**",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.now())
            e_obj.add_field(name='Reason',
                            value=f"```{reason}```\n" +
                            "**Please refrain from this kind of behaviour in the future. Thank you.**")

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
            dt = datetime.datetime.now(pytz.utc)
            record.date = dt.timestamp()

            logger.info(f"[Ban ban()] User kicked from guiled at {dt}.")

            # report to council
            e_obj = discord.Embed(title="Ban Hammer Deployed",
                                  colour=discord.Color.red())

            e_obj.add_field(name="Banned User", value=f"**{ban.username}**", inline=True)
            e_obj.add_field(name="Moderator", value=f"**{record.mod}**", inline=True)
            e_obj.add_field(name="Reason", value=f"```{record.reason}```", inline=False)
            e_obj.add_field(name="User Notified via DM", value="*YES*\n" if dm else "*NO*\n*USER HAS DM's DISABLED*",
                            inline=False)
            e_obj.set_footer(text="Moderator Action")
            if e_obj:
                e_obj.timestamp = dt
                await self.mod_channel.send(embed=e_obj)
            logger.info(f"[Ban ban()] Message sent to mod channel,{self.mod_channel}, of the ban for {ban.username}.")

            # add ban and record objects to lists
            bans.append(ban)
            records.append(record)

        # update database
        await BannedUsers.insert_bans(bans)
        await BanRecords.insert_records(records)

    @commands.command()
    async def unban(self, ctx, user_id: int):
        """Unbans a user"""

        logger.info(f"[Ban unban()] unban command detected from {ctx.author} with args=[ {user_id} ]")
        if user_id not in self.ban_list:
            logger.info(f"Provided id: {user_id}, does not belong to a banned member.")
            e_obj = await em(ctx, title="Error",
                             content=[("Problem",
                                       f"`{user_id}` is either not a valid Discord ID **OR** is not a banned user.")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)
            return

        # "unban"
        self.ban_list.remove(user_id)

        name = await BannedUsers.del_banned_user_by_id(user_id)

        logger.info(f"[Ban unban()] User: {name} with id: {user_id} was unbanned.")
        e_obj = await em(ctx, title="Unban", description=f"**`{name}`** was unbanned.", colour=discord.Color.red())
        if e_obj:
            await self.mod_channel.send(embed=e_obj)

    @unban.error
    async def unban_error(self, ctx, error):
        """Catches an error in unban when a non integer is passed in as an argument"""

        logger.info("[Ban Unban_error] caught non integer ID passed into unban parameter. Handled accordingly")
        if isinstance(error, commands.BadArgument):
            e_obj = await em(ctx, title="Error",
                             content=[("Problem", "Please enter a numerical Discord ID.")],
                             colour=self.error_colour,
                             footer="Command Error")
            if e_obj:
                await ctx.send(embed=e_obj)

    @commands.command()
    async def bans(self, ctx):
        """Gets all banned users"""

        logger.info(f"[Ban bans()] bans command detected from {ctx.author}")

        bans = await BannedUsers.get_all_bans()
        logger.info(f"[Ban bans()] retrieved all banned users: {bans}")

        emb = discord.Embed(title="Banned members", color=discord.Color.red())

        names = ""
        ids = ""
        for ban in bans:
            name = ban.username
            user_id = ban.user_id
            if len(names) + len(name) > 1024 or len(ids) + len(user_id) > 1024:
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
        await ctx.send(f"Total number of banned users: {len(bans)}")
        logger.info("[Ban bans()] done sending embeds with banned user lists and total ban count")

    @commands.command()
    async def purgebans(self, ctx):
        """Clears the ban list on the guild."""

        logger.info(f"[Ban purgebans()] purgebans command detected from {ctx.author}")

        bans = await self.bot.guilds[0].bans()
        logger.info(f"[Ban purgebans()] Retrieved list of banned users from guild: {bans}")

        if not bans:
            logger.info("[Ban purgebans()] Ban list is empty. Sending message and ending command.")
            await ctx.send("Ban list is empty. Nothing to purge.")
            return

        for ban in bans:
            logger.info(f"[Ban purgebans()] Unbanning user: {ban}")
            await self.bot.guilds[0].unban(ban.user)

        await ctx.send(f"**GUILD BAN LIST PURGED**\nTotal # of users unbanned: {len(bans)}")
