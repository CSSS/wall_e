import asyncio
import datetime
import importlib
import inspect
import logging
import os
import subprocess
import sys

import discord
import pytz
import requests
from discord.ext import commands

import django_db_orm_settings
from WalleModels.models import CommandStat, Reminder
from resources.utilities.send import send as helper_send

logger = logging.getLogger('wall_e')


class Administration(commands.Cog):

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        if self.config.enabled("database_config", option="DB_ENABLED"):
            import matplotlib
            matplotlib.use("agg")
            import matplotlib.pyplot as plt  # noqa
            self.plt = plt
            import numpy as np  # noqa
            self.np = np
            self.image_parent_directory = ''
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == "LOCALHOST":
                image_parent_directory = self.config.get_config_value(
                    "basic_config", option="FOLDER_FOR_FREQUENCY_IMAGES"
                )
                if os.path.isdir(image_parent_directory):
                    self.image_parent_directory = image_parent_directory

    def valid_cog(self, name):
        for cog in self.config.get_cogs():
            if cog["name"] == name:
                return True, cog["path"]
        return False, ''

    @commands.command()
    async def pg_dump(self, ctx):
        """
        create the sql by doing
        ssh jenkins.sfucsss.org
        docker exec -it PRODUCTION_MASTER_wall_e_db pg_dump -U postgres --data-only \
         csss_discord_db > csss_discord_db.sql
        scp jenkins.sfucsss.org:/home/jace/csss_discord_db.sql wall_e/src/.

        :param ctx:
        :return:
        """
        commands = False
        reminders = False
        tz = pytz.timezone(django_db_orm_settings.TIME_ZONE)
        await ctx.send("trying to get sql file")
        try:
            sql_lines = requests.get(f"{ctx.message.attachments[0].url}").text.split("\r\n")
        except Exception as e:
            await ctx.send(f"Unable to get sql files for attachment due to issue:```{e}```")
            return
        await ctx.send("sql file received, will now iterate over its lines")
        for line in sql_lines:
            if 'COPY public.commandstats ' in line:
                commands = True
            elif 'COPY public.reminders ' in line:
                reminders = True
            else:
                if line == "\\.":
                    commands = reminders = False
                line = line.split("\t")
                if commands:
                    try:
                        epoch_time = int(line[0])
                        year = int(line[1])
                        month = int(line[2])
                        day = int(line[3])
                        hour = int(line[4])
                        channel_name = line[5]
                        command = line[6]
                        invoked_with = line[7]
                        invoked_subcommand = line[8]
                        await CommandStat.save_command_async(
                            CommandStat(
                                epoch_time=epoch_time, year=year, month=month, day=day, hour=hour,
                                channel_name=channel_name, command=command, invoked_with=invoked_with,
                                invoked_subcommand=invoked_subcommand
                            )
                        )
                    except Exception:
                        print(f"unable to save commandStat {line}")
                elif reminders:

                    try:
                        date_to_be_reminded_epoch = line[1]
                        message = line[2]
                        author_id = int(line[3])
                        date_to_be_reminded_epoch = tz.localize(
                            datetime.datetime.strptime(f"{date_to_be_reminded_epoch}", "%Y-%m-%d %H:%M:%S.%f"),
                            is_dst=None
                        )
                        await Reminder.save_reminder(
                            Reminder(
                                reminder_date_epoch=date_to_be_reminded_epoch.timestamp(), message=message,
                                author_id=author_id
                            )
                        )
                    except Exception:
                        print(f"unable to save Reminder {line}")
        await ctx.send("File parsed and saved to DB")

    @commands.command()
    async def exit(self, ctx):
        if 'LOCALHOST' == self.config.get_config_value('basic_config', 'ENVIRONMENT'):
            await self.bot.close()

    @commands.command()
    async def load(self, ctx, name):
        logger.info(f"[Administration load()] load command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(name)
        if not valid:
            await ctx.send(f"```{name} isn't a real cog```")
            logger.info(
                f"[Administration load()] {ctx.message.author} tried loading "
                f"{name} which doesn't exist."
            )
            return
        try:
            cog_file = importlib.import_module(folder + name)
            cog_class_name = inspect.getmembers(sys.modules[cog_file.__name__], inspect.isclass)[0][0]
            cog_to_load = getattr(cog_file, cog_class_name)
            self.bot.add_cog(cog_to_load(self.bot, self.config))
            await ctx.send(f"{name} command loaded.")
            logger.info(f"[Administration load()] {name} has been successfully loaded")
        except(AttributeError, ImportError) as e:
            await ctx.send(f"command load failed: {type(e)}, {e}")
            logger.info(f"[Administration load()] loading {name} failed :{type(e)}, {e}")

    @commands.command()
    async def unload(self, ctx, name):
        logger.info(f"[Administration unload()] unload command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(name)
        if not valid:
            await ctx.send(f"```{name} isn't a real cog```")
            logger.info(
                f"[Administration load()] {ctx.message.author} tried loading "
                f"{name} which doesn't exist."
            )
            return
        cog_file = importlib.import_module(folder + name)
        cog_class_name = inspect.getmembers(sys.modules[cog_file.__name__], inspect.isclass)[0][0]
        self.bot.remove_cog(cog_class_name)
        await ctx.send(f"{name} command unloaded")
        logger.info(f"[Administration unload()] {name} has been successfully loaded")

    @commands.command()
    async def reload(self, ctx, name):
        logger.info(f"[Administration reload()] reload command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(name)
        if not valid:
            await ctx.send(f"```{name} isn't a real cog```")
            logger.info(f"[Administration reload()] {ctx.message.author} tried "
                        f"loading {name} which doesn't exist.")
            return
        cog_file = importlib.import_module(folder + name)
        cog_class_name = inspect.getmembers(sys.modules[cog_file.__name__], inspect.isclass)[0][0]
        self.bot.remove_cog(cog_class_name)
        try:
            cog_to_load = getattr(cog_file, cog_class_name)
            self.bot.add_cog(cog_to_load(self.bot, self.config))
            await ctx.send(f"`{folder + name} command reloaded`")
            logger.info(f"[Administration reload()] {name} has been successfully reloaded")
        except(AttributeError, ImportError) as e:
            await ctx.send(f"Command load failed: {type(e)}, {e}")
            logger.info(f"[Administration reload()] loading {name} failed :{type(e)}, {e}")

    @commands.command()
    async def exc(self, ctx, *args):
        logger.info("[Administration exc()] exc command detected "
                    f"from {ctx.message.author} with arguments {' '.join(args)}")
        query = " ".join(args)
        # this got implemented for cases when the output of the command is too big to send to the channel
        exit_code, output = subprocess.getstatusoutput(query)
        await helper_send(ctx, f"Exit Code: {exit_code}")
        await helper_send(ctx, output, prefix="```", suffix="```")

    @commands.command()
    async def frequency(self, ctx, *args):
        if self.config.enabled("database_config", option="DB_ENABLED"):
            logger.info("[Administration frequency()] frequency command "
                        f"detected from {ctx.message.author} with arguments [{args}]")
            column_headers = CommandStat.get_column_headers_from_database()
            if len(args) == 0:
                await ctx.send(f"please specify which columns you want to count={column_headers}")
                return
            else:
                for arg in args:
                    if arg not in column_headers:
                        await ctx.send(
                            f"argument '{arg}' is not a valid option\nThe list of options are"
                            f": {column_headers}"
                        )
                        return

            dic_result = sorted(
                (await CommandStat.get_command_stats_dict(args)).items(),
                key=lambda kv: kv[1]
            )
            logger.info("[Administration frequency()] sorted dic_results by value")
            image_path = f"{self.image_parent_directory}image.png"
            if len(dic_result) <= 50:
                logger.info("[Administration frequency()] dic_results's length is <= 50")
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
                fig.savefig(image_path)
                logger.info("[Administration frequency()] graph created and saved")
                self.plt.close(fig)
                await ctx.send(file=discord.File(image_path))
                logger.info("[Administration frequency()] graph image file has been sent")
            else:
                logger.info("[Administration frequency()] dic_results's length is > 50")
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
                    logger.info("[Administration frequency()] creating "
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
                    fig.savefig(image_path)
                    logger.info("[Administration frequency()] graph created and saved")
                    self.plt.close(fig)
                    if msg is None:
                        msg = await ctx.send(file=discord.File(image_path))
                    else:
                        await msg.delete()
                        msg = await ctx.send(file=discord.File(image_path))
                    for reaction in to_react:
                        await msg.add_reaction(reaction)

                    def check_reaction(reaction, user):
                        if not user.bot:  # just making sure the bot doesnt take its own reactions
                            # into consideration
                            e = f"{reaction.emoji}"
                            logger.info(f"[Administration frequency()] reaction {e} detected from {user}")
                            return e.startswith(('⏪', '⏩', '✅'))

                    logger.info("[Administration frequency()] graph image file has been sent")
                    user_reacted = None
                    while user_reacted is None:
                        try:
                            user_reacted = await self.bot.wait_for('reaction_add', timeout=20, check=check_reaction)
                        except asyncio.TimeoutError:
                            logger.info("[Administration frequency()] timed out waiting for the user's reaction.")
                        if user_reacted:
                            if '⏪' == user_reacted[0].emoji:
                                current_page -= 1
                                if current_page < 0:
                                    current_page = number_of_pages - 1
                                logger.info("[Administration frequency()] user indicates they "
                                            f" want to go back to page {current_page}")
                            elif '⏩' == user_reacted[0].emoji:
                                current_page += 1
                                if current_page >= number_of_pages:
                                    current_page = 0
                                logger.info(f"[Administration frequency()] user indicates they want to go to page {current_page}")
                            elif '✅' == user_reacted[0].emoji:
                                logger.info("[Administration frequency()] user "
                                            "indicates they are done with the roles "
                                            "command, deleting roles message")
                                await msg.delete()
                                return
                        else:
                            logger.info("[Administration frequency()] deleting message")
                            await msg.delete()
                            return
                    logger.info("[Administration frequency()] updating first_index "
                               f"and last_index to {first_index} and {last_index} respectively")
