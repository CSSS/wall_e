import asyncio
import datetime
import importlib
import inspect
import re
import subprocess
import sys

import discord
from discord import app_commands
from discord.ext import commands

from utilities.autocomplete.extensions_load_choices import get_extension_that_can_be_loaded, \
    get_extension_that_can_be_unloaded
from utilities.global_vars import wall_e_config, bot

from extensions.manage_test_guild import ManageTestGuild

from utilities.bot_channel_manager import BotChannelManager
from utilities.embed import embed, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.send import send as helper_send
from utilities.setup_logger import Loggers
from wall_e_models.models import CommandStat

from utilities.wall_e_bot import extension_location_python_path

extension_mapping = {}


@bot.event
async def on_app_command_completion(interaction: discord.Interaction, cmd: discord.app_commands.commands.Command):
    """
    Function that gets called whenever a slash command gets called, being use for data gathering purposes
    :param interaction:
    :param cmd:
    :return:
    """
    await save_command_stat(
        interaction.channel.name, interaction.command.name, cmd.qualified_name, None
    )


@bot.listen(name="on_command")
async def save_command_stats(ctx):
    """
    Function that gets called whenever a text commmand gets called, being use for data gathering purposes
    :param ctx: the ctx object that is part of command parameters that are not slash commands
    :return:
    """
    await save_command_stat(
        ctx.channel, ctx.command, invoked_with=ctx.invoked_with, invoked_subcommand=ctx.invoked_subcommand, ctx=ctx
    )


async def save_command_stat(
        channel_name, command_name, invoked_with, invoked_subcommand=None, ctx=None):
    database_enabled = wall_e_config.enabled("database_config", option="ENABLED")
    if ctx is None:
        command_in_correct_channel = wall_e_config.enabled("basic_config", option="ENVIRONMENT") != "TEST"
    else:
        command_in_correct_channel = ManageTestGuild.check_text_command_test_environment(ctx)

    if database_enabled and command_in_correct_channel:
        await CommandStat.save_command_stat(CommandStat(
            epoch_time=datetime.datetime.now().timestamp(), channel_name=channel_name,
            command=command_name, invoked_with=invoked_with,
            invoked_subcommand=invoked_subcommand
        ))


class Administration(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Administration")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[Administration __init__()] initializing Administration")
        self.guild = None
        self.announcement_channel = None

        for extension in wall_e_config.get_extensions():
            extension_module = importlib.import_module(f"{extension_location_python_path}{extension}")
            classes_that_match = inspect.getmembers(sys.modules[extension_module.__name__], inspect.isclass)
            for class_that_match in classes_that_match:
                cog_class_to_load = getattr(extension_module, class_that_match[0])
                cog_class_matches_file_name = (
                    cog_class_to_load.__name__.lower() == extension.lower().replace("_", "")
                )
                if type(cog_class_to_load) is commands.cog.CogMeta and cog_class_matches_file_name:
                    extension_mapping[extension] = class_that_match[0]
        if wall_e_config.enabled("database_config", option="ENABLED"):
            import matplotlib
            matplotlib.use("agg")
            import matplotlib.pyplot as plt  # noqa
            self.plt = plt
            import numpy as np  # noqa
            self.np = np

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def get_announcement_channel(self):
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info("[Administration get_announcement_channel()] acquiring text channel for announcements.")
        reminder_chan_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            "announcements"
        )
        self.announcement_channel = discord.utils.get(self.guild.channels, id=reminder_chan_id)
        self.logger.debug(
            f"[Administration get_announcement_channel()] text channel {self.announcement_channel} acquired."
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path,
                "administration_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
                "administration_warn"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path,
                "administration_error"
            )

    @commands.command()
    async def exit(self, ctx):
        if 'LOCALHOST' == wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'):
            await bot.close()

    @app_commands.command(description="Deletes the log channel and category")
    async def delete_log_channels(self, interaction: discord.Interaction):
        if 'LOCALHOST' == wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'):
            self.logger.info("[Administration delete_log_channels()] delete_log_channels command "
                             f"detected from {interaction.user}")
            await interaction.response.defer()
            await BotChannelManager.delete_log_channels(interaction)
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                description='Log Channels Deleted!',
                author=interaction.client.user,
            )
            if e_obj is not False:
                await interaction.followup.send(embed=e_obj)
        else:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                description='This command only work when doing dev work',
                author=interaction.client.user,
            )
            if e_obj is not False:
                await interaction.followup.send(embed=e_obj)

    @app_commands.command(description="Deletes last X messages from channel")
    async def purge_messages(self, interaction: discord.Interaction, last_x_messages_to_delete: int):
        if 'LOCALHOST' == wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'):
            self.logger.info("[Administration purge_messages()] purge_messages command "
                             f"detected from {interaction.user}")
            await interaction.response.defer()
            messages = [message async for message in interaction.channel.history(
                limit=last_x_messages_to_delete+2  # adding 2,
                # one is to account for the invoking slash command's message
                # and the other is to ensure that the message that will be used as the after parameter is retrieved
            )]
            messages.reverse()
            if len(messages) < last_x_messages_to_delete+1:  # adding 1 to account for the
                # invoking slash command's message
                e_obj = await embed(
                    self.logger,
                    interaction=interaction,
                    description=f'There are not {last_x_messages_to_delete} messages to delete',
                    author=interaction.client.user,
                )
                send_func = interaction.followup.send
            else:
                if len(messages) == last_x_messages_to_delete+1:
                    after_message = None
                else:
                    after_message = messages[0]
                self.logger.debug(f"deleting {last_x_messages_to_delete} messages")
                await interaction.channel.purge(after=after_message, bulk=True)
                e_obj = await embed(
                    self.logger,
                    interaction=interaction,
                    description=f'Last {last_x_messages_to_delete} message[s] deleted',
                    author=interaction.client.user,
                )
                send_func = interaction.channel.send
            if e_obj is not None:
                msg = await send_func(embed=e_obj)
                await asyncio.sleep(5)
                await msg.delete()
        else:
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                description='This command only work when running wall_e on your local machine',
                author=interaction.client.user,
            )
            if e_obj is not False:
                await interaction.response.send_message(embed=e_obj)

    @app_commands.command(name="load", description="loads the specified extension")
    @app_commands.describe(extension_to_load="extension to load")
    @app_commands.autocomplete(extension_to_load=get_extension_that_can_be_loaded)
    @app_commands.checks.has_any_role("Bot_manager", "Minions", "Moderator")
    async def load(self, interaction: discord.Interaction, extension_to_load: str):
        self.logger.info(f"[Administration load()] load command detected from {interaction.user}")
        await interaction.response.defer()
        if extension_to_load not in wall_e_config.get_extensions():
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid extension **`{extension_to_load}`** specified. Please select from the list.",
                colour=WallEColour.ERROR
            )
            await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        try:
            await bot.load_extension(extension_to_load)
            await self.sync_helper(interaction=interaction)
            await interaction.followup.send(f"`{extension_to_load}` extension loaded.")
            self.logger.debug(f"[Administration load()] {extension_to_load} has been successfully loaded")
        except(AttributeError, ImportError) as e:
            await interaction.followup.send(f"{extension_to_load}` extension load failed: {type(e)}, {e}")
            self.logger.error(f"[Administration load()] loading {extension_to_load} failed :{type(e)}, {e}")

    @app_commands.command(name="unload", description="unloads the specified extension")
    @app_commands.describe(extension_to_unload="extension to unload")
    @app_commands.autocomplete(extension_to_unload=get_extension_that_can_be_unloaded)
    @app_commands.checks.has_any_role("Bot_manager", "Minions", "Moderator")
    async def unload(self, interaction: discord.Interaction, extension_to_unload: str):
        self.logger.info(f"[Administration unload()] unload command detected from {interaction.user}")
        await interaction.response.defer()
        if extension_to_unload not in wall_e_config.get_extensions():
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid extension **`{extension_to_unload}`** specified. Please select from the list.",
                colour=WallEColour.ERROR
            )
            await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        await bot.unload_extension(extension_to_unload)
        await self.sync_helper(interaction=interaction)
        await interaction.followup.send(f"`{extension_to_unload}` extension unloaded.")
        self.logger.debug(f"[Administration unload()] {extension_to_unload} has been successfully loaded")

    @app_commands.command(name="reload", description="reloads the specified extension")
    @app_commands.describe(extension_to_reload="extension to reload")
    @app_commands.autocomplete(extension_to_reload=get_extension_that_can_be_unloaded)
    @app_commands.checks.has_any_role("Bot_manager", "Minions", "Moderator")
    async def reload(self, interaction: discord.Interaction, extension_to_reload: str):
        self.logger.info(f"[Administration reload()] reload command detected from {interaction.user}")
        await interaction.response.defer()
        if extension_to_reload not in wall_e_config.get_extensions():
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                author=interaction.client.user,
                description=f"Invalid extension **`{extension_to_reload}`** specified. Please select from the list.",
                colour=WallEColour.ERROR
            )
            await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        try:
            await bot.reload_extension(extension_to_reload)
            await self.sync_helper(interaction=interaction)
            await interaction.followup.send(f"`{extension_to_reload}` extension reloaded.")
            self.logger.debug(f"[Administration reload()] {extension_to_reload} has been successfully reloaded")
        except(AttributeError, ImportError) as e:
            await interaction.followup.send(f"{extension_to_reload}` extension reload failed: {type(e)}, {e}")
            self.logger.debug(f"[Administration reload()] reloading {extension_to_reload} failed :{type(e)}, {e}")

    @commands.command(
        brief="executes the command on the bot host OS",
        help=(
            'Arguments:\n'
            '---command to run: the command to run on the host OS\n\n'
            'Example:\n'
            '---.exc ls -l\n\n'
        ),
        usage='command to run'
    )
    @commands.has_role("Bot_manager")
    async def exc(self, ctx, *command):
        self.logger.info("[Administration exc()] exc command detected "
                         f"from {ctx.message.author} with arguments {' '.join(command)}")
        command = " ".join(command)
        # this got implemented for cases when the output of the command is too big to send to the channel
        exit_code, output = subprocess.getstatusoutput(command)
        await helper_send(self.logger, ctx, f"Exit Code: {exit_code}", reference=ctx.message)
        await helper_send(self.logger, ctx, output, prefix="```", suffix="```", reference=ctx.message)

    @commands.command(brief="resyncs the slash commands in wall_e to this discord guild")
    @commands.has_role("Bot_manager")
    async def sync(self, ctx):
        self.logger.info(f"[AdministrationAdministration sync()] sync command detected from {ctx.message.author}")
        await ctx.message.delete()
        await self.sync_helper(ctx=ctx)

    async def sync_helper(self, ctx=None, interaction=None):
        message = "Testing guild does not provide support for Slash Commands" \
            if wall_e_config.get_config_value("basic_config", "ENVIRONMENT") == 'TEST' \
            else 'Commands Synced!'
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            interaction=interaction,
            description=message,
            author=ctx.me if interaction is None else interaction.client.user,
        )
        if wall_e_config.get_config_value("basic_config", "ENVIRONMENT") != 'TEST':
            await bot.tree.sync(guild=self.guild)
        if e_obj is not False:
            send_func = ctx.send if interaction is None else interaction.channel.send
            message = await send_func(embed=e_obj)
            await asyncio.sleep(10)
            await message.delete()

    @commands.command(
        brief="sends an announcement to the announcement channel",
        help=(
            'Arguments:\n'
            '---the announcement: the announcement to post to the announcement channel\n\n'
            'Example:\n'
            '---.announce the example\n\n'
        ),
        usage='the announcement',
    )
    @commands.has_role("Bot_manager")
    async def announce(self, ctx, *message):
        self.logger.info(f"[Administration announce()] announce command detected from {ctx.message.author}")
        message = list(message)
        matched_strings = re.findall(r"https://discord.com/channels/\d*/\d*/\d*", message[len(message) - 1])
        reference = None
        if len(matched_strings) == 1:
            message.pop(len(message)-1)
            ids = matched_strings[0].split("/")
            channel_id = int(ids[5])
            message_id = int(ids[6])
            reference_channel = discord.utils.get(self.guild.channels, id=channel_id)
            reference = await reference_channel.fetch_message(message_id)
        await self.announcement_channel.send("\n".join(message), reference=reference)
        await ctx.message.delete()

    @commands.command(
        brief="creates a graph to show some command usage statistics.",
        help=(
            'the different way to count up the command usage are: command, year, month, day, hour, channel_aliases, '
            'invoked_with, invoked_subcommand.\n'
            'You may optionally choose to group the entries such that all the times that a certain command was '
            'executed on a certain day are counted together.'
            'You can do this with the command ".frequency command day"\n\n'
            'Arguments:\n'
            '---the stat [the stat]: the grouping to use when calculating the stats and graph\n\n'
            'Example:\n'
            '---.frequency command -> creates a graph that shows the usage breakdown by command\n'
            '---.frequency day -> creates a graph that shows the usage breakdown by day\n'
            '---.frequency command hour -> creates a graph that shows the usage breakdown by command and hour\n\n'
        ),
        usage='the stat',
    )
    @commands.has_role("Bot_manager")
    async def frequency(self, ctx, *args):
        if wall_e_config.enabled("database_config", option="ENABLED"):
            self.logger.info("[Administration frequency()] frequency command "
                             f"detected from {ctx.message.author} with arguments [{args}]")
            column_headers = CommandStat.get_column_headers_from_database()
            if len(args) == 0:
                await ctx.send(
                    f"please specify which columns you want to count={column_headers}", reference=ctx.message
                )
                return
            else:
                for arg in args:
                    if arg not in column_headers:
                        await ctx.send(
                            f"argument '{arg}' is not a valid option\nThe list of options are"
                            f": {column_headers}", reference=ctx.message
                        )
                        return

            dic_result = sorted(
                (await CommandStat.get_command_stats_dict(args)).items(),
                key=lambda kv: kv[1]
            )
            self.logger.debug("[Administration frequency()] sorted dic_results by value")
            image_name = "image.png"
            if len(dic_result) <= 50:
                self.logger.debug("[Administration frequency()] dic_results's length is <= 50")
                labels = [i[0] for i in dic_result]
                numbers = [i[1] for i in dic_result]
                self.plt.rcdefaults()
                fig, ax = self.plt.subplots()
                y_pos = self.np.arange(len(labels))
                for i, v in enumerate(numbers):
                    ax.text(v, i + .25, f"{v}", color='blue', fontweight='bold')
                ax.barh(y_pos, numbers, align='center', color='green')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels)
                ax.invert_yaxis()  # labels read top-to-bottom
                if len(args) > 1:
                    title = '-'.join(f"{arg}" for arg in args[:len(args) - 1])
                    title += f"-{args[len(args) - 1]}"
                else:
                    title = args[0]
                ax.set_title(f"How may times each {title} appears in the database since Sept 21, 2018")
                fig.set_size_inches(18.5, 10.5)
                fig.savefig(image_name)
                self.logger.debug("[Administration frequency()] graph created and saved")
                self.plt.close(fig)
                await ctx.send(file=discord.File(image_name), reference=ctx.message)
                self.logger.debug("[Administration frequency()] graph image file has been sent")
            else:
                self.logger.debug("[Administration frequency()] dic_results's length is > 50")
                number_of_pages = int(len(dic_result) / 50)
                if len(dic_result) % 50 != 0:
                    number_of_pages += 1
                number_of_bars_per_page = int(len(dic_result) / number_of_pages) + 1
                msg = None
                current_page = 0

                first_index = 0
                last_index = number_of_bars_per_page - 1
                boundaries_for_each_page = {}
                for page in range(0, number_of_pages):
                    boundaries_for_each_page[page] = {
                        'first_index': first_index,
                        'last_index': last_index
                    }
                    first_index += number_of_bars_per_page
                    last_index += number_of_bars_per_page

                while True:
                    self.logger.debug("[Administration frequency()] creating "
                                      f"a graph with entries {first_index} to {last_index}")
                    to_react = ['⏪', '⏩', '✅']
                    first_index = boundaries_for_each_page[current_page]['first_index']
                    last_index = boundaries_for_each_page[current_page]['last_index']
                    labels = [i[0] for i in dic_result][first_index:last_index]
                    numbers = [i[1] for i in dic_result][first_index:last_index]
                    self.plt.rcdefaults()
                    fig, ax = self.plt.subplots()
                    y_pos = self.np.arange(len(labels))
                    for i, v in enumerate(numbers):
                        ax.text(v, i + .25, f"{v}", color='blue', fontweight='bold')
                    ax.barh(y_pos, numbers, align='center', color='green')
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(labels)
                    ax.invert_yaxis()  # labels read top-to-bottom
                    ax.set_xlabel(f"Page {current_page}/{number_of_pages - 1}")
                    if len(args) > 1:
                        title = '_'.join(f"{arg}" for arg in args[:len(args) - 1])
                        title += f"_{args[len(args) - 1]}"
                    else:
                        title = args[0]
                    ax.set_title(f"How may times each {title} appears in the database since Sept 21, 2018")
                    fig.set_size_inches(30, 10.5)
                    fig.savefig(image_name)
                    self.logger.debug("[Administration frequency()] graph created and saved")
                    self.plt.close(fig)
                    if msg is None:
                        msg = await ctx.send(file=discord.File(image_name), reference=ctx.message)
                    else:
                        await msg.delete()
                        msg = await ctx.send(file=discord.File(image_name), reference=ctx.message)
                    for reaction in to_react:
                        await msg.add_reaction(reaction)

                    def check_reaction(reaction, user):
                        if not user.bot:  # just making sure the bot doesnt take its own reactions
                            # into consideration
                            e = f"{reaction.emoji}"
                            self.logger.debug(f"[Administration frequency()] reaction {e} detected from {user}")
                            return e.startswith(('⏪', '⏩', '✅'))

                    self.logger.debug("[Administration frequency()] graph image file has been sent")
                    user_reacted = None
                    while user_reacted is None:
                        try:
                            user_reacted = await bot.wait_for('reaction_add', timeout=20, check=check_reaction)
                        except asyncio.TimeoutError:
                            self.logger.debug(
                                "[Administration frequency()] timed out waiting for the user's reaction."
                            )
                        if user_reacted:
                            if '⏪' == user_reacted[0].emoji:
                                current_page -= 1
                                if current_page < 0:
                                    current_page = number_of_pages - 1
                                self.logger.debug("[Administration frequency()] user indicates they "
                                                  f" want to go back to page {current_page}")
                            elif '⏩' == user_reacted[0].emoji:
                                current_page += 1
                                if current_page >= number_of_pages:
                                    current_page = 0
                                self.logger.debug(
                                    "[Administration frequency()] user indicates they "
                                    f"want to go to page {current_page}"
                                )
                            elif '✅' == user_reacted[0].emoji:
                                self.logger.debug("[Administration frequency()] user "
                                                  "indicates they are done with the roles "
                                                  "command, deleting roles message")
                                await msg.delete()
                                return
                        else:
                            self.logger.debug("[Administration frequency()] deleting message")
                            await msg.delete()
                            return
                    self.logger.debug("[Administration frequency()] updating first_index "
                                      f"and last_index to {first_index} and {last_index} respectively")


async def setup(bot):
    await bot.add_cog(Administration())
