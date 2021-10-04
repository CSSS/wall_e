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
        self.errorColour = 0xA6192E

    @commands.Cog.listener(name='on_ready')
    async def load(self):
        """Grabs channel to send mod reports to and reads in the blacklist from db"""
        report_channel = self.config.get_config_value('basic_config', 'COUNCIL_REPORT_CHANNEL')
        logger.info(f'[Ban load()] Attempting to get the report channel: {report_channel}')

        self.mod_channel = discord.utils.get(self.bot.guilds[0].channels, name=report_channel)
        logger.info(f"[Ban info()] #{report_channel} channel {'successfully' if self.mod_channel else 'not'} found")

        # read in blacklist of banned users
        logger.info('[Ban load] loading ban list from the database')
        self.ban_list = await BannedUsers.get_banned_ids()
        logger.info(f"[Ban load()] loaded the following banned users: {self.ban_list}")

    @commands.Cog.listener(name='on_member_join')
    async def watchdog(self, member: discord.Member):
        """Watches for users joining the guild and kicks and bans a user if they are banned"""

        if member.id in self.ban_list:
            logger.info(f"[Ban watchdog()] banned member, {member}, detected. Promply will notify and kick them.")

            e_obj = discord.Embed(title="Ban Notification",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.now(pytz.timezone('Canada/Pacific'))
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
        username = member.name + '#' + member.discriminator
        mod = audit_ban.user.name + '#' + audit_ban.user.discriminator
        mod_id = audit_ban.user.id
        date = audit_ban.created_at
        reason = audit_ban.reason if audit_ban.reason else 'No Reason Given!'

        # update blacklist and db
        self.ban_list.append(member.id)
        await BannedUsers.insert_ban(username, member.id)
        await BanRecords.insert_record(username, member.id, mod, mod_id, date, reason)

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
        """Reads in all guild bans into this ban system"""

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
            audit_users.append(ban.target.id)

            ban_data.append([ban.target.name+'#'+ban.target.discriminator,
                             ban.target.id,
                             ban.user.name+'#'+ban.user.discriminator,
                             ban.user.id,
                             pytz.utc.localize(ban.created_at),
                             ban.reason if ban.reason else 'No Reason Given!'
                             ])

        for ban in bans:
            if ban.user.id in audit_users:
                continue
            ban_data.append([ban.user.name+'#'+ban.user.discriminator,
                             ban.user.id,
                             None,
                             None,
                             None,
                             'No Reason Given!'
                             ])

        # push to db and blacklist
        for ban in ban_data:
            if ban[1] in ban_ids:
                self.ban_list.append(ban[1])
                await BannedUsers.insert_ban(ban[0], ban[1])

            await BanRecords.insert_record(ban[0], ban[1], ban[2], ban[3], ban[4], ban[5])
        await ctx.send(f"{len(ban_data)} moved from guild bans to db.")
        logger.info(f"[Ban initban()] total of {len(ban_data)} bans moved into db")

    @commands.command()
    async def ban(self, ctx, *args):
        """Bans a user from the guild"""

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
            self.ban_list.append(user.id)

            # dm banned user
            e_obj = discord.Embed(title="Ban Notification",
                                  description="**You've been PERMANENTLY BANNED from" +
                                              f"{self.bot.guilds[0].name.upper()}.**",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.now(pytz.timezone('Canada/Pacific')))

            e_obj.add_field(name='Reason',
                            value=f"```{reason}```\n" +
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
            dt = datetime.datetime.now(pytz.utc)
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
            await BannedUsers.insert_ban(username, user.id)
            await BanRecords.insert_record(username, user.id, mod_info[0], mod_info[1], dt, reason)

    @commands.command()
    async def unban(self, ctx, _id: int):
        """Unbans a user"""

        logger.info(f"[Ban unban()] unban command detected from {ctx.author} with args=[ {_id} ]")
        if _id not in self.ban_list:
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
        self.ban_list.remove(_id)

        name = await BannedUsers.del_banned_user_by_id(_id)

        logger.info(f"[Ban unban()] User: {name} with id: {_id} was unbanned.")
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
                             colour=self.errorColour,
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
        for row in bans:
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
        await ctx.send(f"Total number of banned users: {len(bans)}")
        logger.info("[Ban bans()] done sending embeds with banned user lists and total ban count")
