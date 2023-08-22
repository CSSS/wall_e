import datetime
import logging
import re
import sys
import traceback

import discord
from discord.ext import commands

from WalleModels.models import CommandStat
from resources.utilities.embed import embed as imported_embed
from resources.utilities.list_of_perms import get_list_of_user_permissions

logger = logging.getLogger('wall_e')


class ManageCog(commands.Cog):

    def __init__(self, bot, config):
        logger.info("[ManageCog __init__()] initializing the TestCog")
        bot.add_check(self.check_test_environment)
        bot.add_check(self.check_privilege)
        self.bot = bot
        self.config = config
        self.help_dict = self.config.get_help_json()

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        logger.info(f"[ManageCog debuginfo()] debuginfo command detected from {ctx.message.author}")
        if self.config.get_config_value("basic_config", "ENVIRONMENT") == 'TEST':
            await ctx.send(
                '```You are testing the latest commit of branch or pull request: '
                f'{self.config.get_config_value("basic_config", "BRANCH_NAME")}```'
            )
        return

    # this check is used by the TEST guild to ensur that each TEST container will only process incoming commands
    # that originate from channels that match the name of their branch
    def check_test_environment(self, ctx):
        test_guild = self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST'
        correct_test_guild_text_channel = (
            ctx.message.guild is not None and
            (ctx.channel.name == f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
             or
             ctx.channel.name == self.config.get_config_value('basic_config', 'BRANCH_NAME').lower())
        )
        if not test_guild:
            return True
        return correct_test_guild_text_channel

    # this check is used to ensure that users can only access commands that they have the rights to
    async def check_privilege(self, ctx):
        command_used = f"{ctx.command}"
        if command_used == "exit":
            return True
        if command_used not in self.help_dict:
            return False
        command_info = self.help_dict[command_used]
        if command_info['access'] == 'roles':
            user_roles = [
                role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
            ]
            shared_roles = set(user_roles).intersection(command_info['roles'])
            if len(shared_roles) == 0:
                await ctx.send(
                    "You do not have adequate permission to execute this command, incident will be reported"
                )
            return (len(shared_roles) > 0)
        if command_info['access'] == 'permissions':
            user_perms = await get_list_of_user_permissions(ctx)
            shared_perms = set(user_perms).intersection(command_info['permissions'])
            if (len(shared_perms) == 0):
                await ctx.send(
                    "You do not have adequate permission to execute this command, incident will be reported"
                )
            return (len(shared_perms) > 0)
        return False

    ########################################################
    # Function that gets called whenever a commmand      ##
    # gets called, being use for data gathering purposes ##
    ########################################################
    @commands.Cog.listener()
    async def on_command(self, ctx):
        if self.check_test_environment(ctx) and self.config.enabled("database_config", option="DB_ENABLED"):
            await CommandStat.save_command_async(CommandStat(
                epoch_time=datetime.datetime.now().timestamp(), channel_name=ctx.channel,
                command=ctx.command, invoked_with=ctx.invoked_with,
                invoked_subcommand=ctx.invoked_subcommand
            ))

    ####################################################
    # Function that gets called when the script cant ##
    # understand the command that the user invoked   ##
    ####################################################
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if self.check_test_environment(ctx):
            if isinstance(error, commands.MissingRequiredArgument):
                logger.error(f'[ManageCog on_command_error()] Missing argument: {error.param}')
                e_obj = await imported_embed(
                    ctx=ctx,
                    author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=f"Missing argument: {error.param}"
                )
                if e_obj is not False:
                    await ctx.send(embed=e_obj)
            elif isinstance(error, commands.errors.CommandNotFound):
                return
            else:
                # only prints out an error to the log if the string that was entered doesnt contain just "."
                pattern = r'[^\.]'
                if re.search(pattern, f"{error}"[9:-14]):
                    if type(error) is discord.ext.commands.errors.CheckFailure:
                        logger.warning(
                            f"[ManageCog on_command_error()] user {ctx.author} "
                            "probably tried to access a command they arent supposed to"
                        )
                    else:
                        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                        return

    # this command is used by the TEST guild to create the channel from which this TEST container will process
    # commands
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"[ManageCog on_ready()] acquired {len(self.bot.guilds[0].channels)} channels")
        if self.config.get_config_value("basic_config", "ENVIRONMENT") == 'TEST':
            logger.info("[ManageCog on_ready()] ENVIRONMENT detected to be 'TEST' ENVIRONMENT")
            channels = self.bot.guilds[0].channels
            branch_name = self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
            if discord.utils.get(channels, name=branch_name) is None:
                logger.info(
                    "[ManageCog on_ready()] creating the text channel "
                    f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}"
                )
                await self.bot.guilds[0].create_text_channel(branch_name)
