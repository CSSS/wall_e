# Commands for finding who has access to certain channels.
# Useful since the server size does not allow offline users to be listed
#     in the sidebar
import asyncio

import discord
from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class Here(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Here")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.logger.info("[Here __init__()] initializing Here")
        self.guild = None

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "here_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "here_error"
            )

    def build_embed(self, members, channel):
        # build response

        title = f"Users in **#{channel.name}**"

        self.logger.info(f"[Here build_embed()] creating an embed with title \"{title}\"")
        embed = discord.Embed(type="rich")
        embed.title = title
        embed.color = discord.Color.blurple()
        embed.set_footer(text="brenfan", icon_url="https://i.imgur.com/vlpCuu2.jpg")
        if len(members) == 0:
            string = "I couldnt find anyone.\n"
        elif len(members) > 50:
            string = "There's a lot of people here.\n"
        else:
            string = f"The following ({len(members)}) users have permission for this channel.\n"

            # newline separated lists of members and their nicknames
            nicks = "\n".join([member.display_name for member in members])
            names = "\n".join([str(member) for member in members])

            embed.add_field(name="Name", value=nicks, inline=True)
            embed.add_field(name="Account", value=names, inline=True)

        # comma separated list of role names for each role in the channel
        # if they can read messages
        # like how it says...
        roles = ", ".join([role.name
                           for role in channel.changed_roles
                           if role.permissions.read_messages])
        roles += "\n*This message will self-destruct in 5 minutes*\n"

        embed.add_field(name="Channel Specific Roles", value=roles, inline=False)
        embed.description = string
        return embed

    @commands.command(
        brief="Displays users with permission to view the current channel.",
        help=(
            'Results can be filtered by looking for users whose useraliases or nickaliases on the '
            'server contains the substring indicated with any of the included strings or all '
            'users if no args are given. Multiple may be entered.\n\n'
            'Arguments:\n'
            '---the filter: the filter to apply the users through\n\n'
            'Example:\n'
            '---.here ab\n\n'
        ),
        usage='"the filter"'
    )
    async def here(self, ctx, *search):
        self.logger.info(
            f"[Here here()] {ctx.message.author} called here with {len(search)} arguments: {', '.join(search)}"
        )

        # find people in the channel
        channel = ctx.channel
        members = channel.members

        # optional filtering
        if len(search) > 0:
            # don't ask
            allowed = [m for m in members
                       if len([query for query in search
                               if query.lower() in m.display_name.lower() or query.lower() in str(m).lower()]) > 0]
            members = allowed

        self.logger.info(f"[Here here()] found {len(members)} users in {channel.name}")

        embed = self.build_embed(members, channel)

        await ctx.send(embed=embed, delete_after=300)


async def setup(bot):
    await bot.add_cog(Here())
