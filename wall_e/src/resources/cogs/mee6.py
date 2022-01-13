import asyncio
import json
import logging

import discord
import requests
from discord.ext import commands

from WalleModels.models import Level
from WalleModels.models import UserPoint
from resources.utilities.embed import embed

logger = logging.getLogger('wall_e')


class Mee6(commands.Cog):

    def __init__(self, bot, config):
        """

        :param bot:
        :param config:
        """
        self.levels_have_been_changed = True
        self.bot = bot
        self.config = config
        self.user_points = {}
        self.levels = {}
        self.database_and_dict_populated = False
        self.xp_system_ready = False
        self.bot_channel = None
        self.council_channel = None
        self.bot.loop.create_task(self.load_data_from_mee6_endpoint_and_json())
        self.bot.loop.create_task(self.ensure_roles_exist_and_have_right_users())

    async def load_data_from_mee6_endpoint_and_json(self):
        """

        :return:
        """
        await self.bot.wait_until_ready()
        await self.get_bot_general_channel()
        await self.bot_channel.send("loading XP commands......")
        if not await Level.level_points_have_been_imported():
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading levels into DB and dict")
            with open('resources/mee6_levels/levels.json') as f:
                self.levels = {
                    level_number: await Level.create_level(
                        level_number,
                        level_info['total_xp_required_for_level'],
                        level_info['xp_needed_to_level_up_to_next_level'],
                        role_name=level_info['role_name'] if 'role_name' in level_info else None,
                    )
                    for (level_number, level_info) in json.load(f).items()
                }
        elif len(self.levels) == 0:
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading level from DB into dict")
            self.levels = await Level.load_to_dict()
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] levels loaded in DB and dict")

        if not await UserPoint.user_points_have_been_imported():
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading user cls into DB and dict")
            page = 0
            all_users_loaded = False
            while not all_users_loaded:
                r = requests.get(
                    f"https://mee6.xyz/api/plugins/levels/leaderboard/228761314644852736?page={page}&limit=1000"
                )
                if r.status_code == 200:
                    data = json.loads(r.text)
                    if len(data['players']) > 0:
                        page += 1
                        for player in data['players']:
                            # player = {
                            #     'avatar': '3fd2cc8fda2a0af3b1a06bb27d5151f0',
                            #     'detailed_xp': [
                            #         8349,  # how much of the "XP needed to level up" I have so far
                            #         11980,  # XP needed to level up
                            #         197219  # Total XP I have so far
                            #     ],
                            #     'discriminator': '6816',
                            #     'guild_id': '228761314644852736',
                            #     'id': '288148680479997963',
                            #     'level': 44,
                            #     'message_count': 9858,  # total messages sent
                            #     'username': 'modernNeo',
                            #     'xp': 197219  # Total XP
                            # }
                            user_id = int(player['id'])
                            message_count = int(player['message_count'])
                            level = int(player['level'])
                            user_xp = int(player['xp'])
                            self.user_points[user_id] = await UserPoint.create_user_point(
                                user_id, points=user_xp, message_count=message_count, level=level
                            )
                    else:
                        all_users_loaded = True
        elif len(self.user_points) == 0:
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading user cls from DB into dict")
            self.user_points = await UserPoint.load_to_dict()
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] user cls loaded in DB and dict")
        self.database_and_dict_populated = True

    async def get_bot_general_channel(self):
        """
        gets the bot channel that the commands in the RoleCommands class are limited to operating in. Due to the fact
        that the reminder class was the first class to utilize that bot channel in a specific way and is already
        handling its detection and possible creation, the RoleCommands class will just wait approximately 100 seconds
        to give the reminder class a chance to create the bot channel before exiting if the RoleCommands class cannot
        find the bot channel.
        """
        await self.bot.wait_until_ready()
        bot_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')
        environment = self.config.get_config_value('basic_config', 'ENVIRONMENT')
        self.bot_channel = None
        if environment == 'PRODUCTION' or environment == 'LOCALHOST':
            logger.info(
                f"[Mee6 load_data_from_mee6_endpoint_and_json()] bot_channel_name set to {bot_channel_name} for "
                f"environment {environment}"
            )
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        elif environment == 'TEST':
            bot_channel_name = f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
            logger.info(
                f"[Mee6 load_data_from_mee6_endpoint_and_json()] bot_channel_name set to {bot_channel_name} for "
                f"environment {environment}"
            )
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        number_of_retries_to_attempt = 10
        number_of_retries = 0
        while self.bot_channel is None and number_of_retries < number_of_retries_to_attempt:
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] attempt "
                        f"({number_of_retries}/{number_of_retries_to_attempt}) for getting bot_channel ")
            await asyncio.sleep(10)
            number_of_retries += 1
            self.bot_channel = discord.utils.get(self.bot.guilds[0].channels, name=bot_channel_name)
        if self.bot_channel is None:
            logger.info(
                "[Mee6 load_data_from_mee6_endpoint_and_json()] ultimately unable to get the bot_channel. exiting "
                "now."
            )
            await asyncio.sleep(20)  # this is just here so that the above log line gets a chance to get printed to
            # discord
            exit(1)
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] bot_channel acquired.")

        if self.council_channel is None:
            self.council_channel = discord.utils.get(self.bot.guilds[0].channels, name="council")
            if self.council_channel is None:
                logger.info(
                    "[Mee6 load_data_from_mee6_endpoint_and_json()] the council channel does not seem to exist"
                    " exiting now."
                )
                await asyncio.sleep(20)
                # this is just here so that the above log line gets a chance to get printed to discord
                exit(1)

    async def ensure_roles_exist_and_have_right_users(self):
        while not self.database_and_dict_populated:
            await asyncio.sleep(5)
        while True:
            if self.levels_have_been_changed:
                await self.bot_channel.send("loading XP commands......")
                levels_with_a_role = [level for level in self.levels.values() if level.role_name is not None]
                levels_with_a_role.sort(key=lambda level: level.number)
                # ordering level roles in an ascending order

                guild_roles = []
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()]"
                    f" ensuring that all {len(levels_with_a_role)} XP roles exist"
                )
                xp_roles_that_are_missing = {}
                for level_with_role in levels_with_a_role:
                    role = discord.utils.get(self.bot.guilds[0].roles, name=level_with_role.role_name)
                    if role is not None:
                        guild_roles.append(role)
                        level_with_role.role_id = role.id
                        await level_with_role.async_save()
                    else:
                        xp_roles_that_are_missing[level_with_role.role_name] = level_with_role.number
                if len(xp_roles_that_are_missing) == 0:
                    logger.info(
                        "[Mee6 ensure_roles_exist_and_have_right_users()] all"
                        f" {len(levels_with_a_role)} XP roles exist"
                    )
                else:
                    xp_roles_that_are_missing = [
                        f"{role_name} - {role_number}" for role_name, role_number in xp_roles_that_are_missing.items()
                    ]
                    xp_roles_that_are_missing = "\n".join(xp_roles_that_are_missing)
                    await self.council_channel.send(
                        "The following XP roles could not be found. Please call `.remove_level_name <level_number>` "
                        "to confirm that you want the XP roles deleted or re-create the roles:\n\n"
                        "Role Name - Linked XP Level\n"
                        f"{xp_roles_that_are_missing}"
                    )
                members = await self.bot.guilds[0].fetch_members().flatten()
                # sorts the members in ascending order by their total cls
                members_with_points = [member for member in members if member.id in self.user_points]
                members_with_points.sort(key=lambda member: self.user_points[member.id].points)
                role_indx = 0
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensuring that members with cls have the right "
                    "XP roles")
                for member_with_point in members_with_points:
                    if (
                            self.user_points[member_with_point.id].points >=
                            levels_with_a_role[role_indx].total_points_required
                    ):
                        role_indx += 1
                    await member_with_point.remove_roles(*guild_roles[role_indx:])
                    await member_with_point.add_roles(*guild_roles[:role_indx])
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensured that the members with cls have the "
                    "right XP roles")

                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensuring that members without cls don't have "
                    "any XP roles "
                )
                for member_without_points in [member for member in members if member.id not in self.user_points]:
                    await member_without_points.remove_roles(*guild_roles)
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensured that members without cls don't have "
                    "any XP roles "
                )
                self.levels_have_been_changed = False
                self.xp_system_ready = True
                await self.bot_channel.send("XP commands are now available")
            await asyncio.sleep(86400)

    @commands.Cog.listener(name='on_message')
    async def on_message(self, message):
        """

        :param message:
        :return:
        """

        if not message.author.bot:
            if not self.xp_system_ready:
                return
            message_author_id = message.author.id
            if message_author_id not in self.user_points:
                logger.info("user not in user_points")
                self.user_points[message_author_id] = await UserPoint.create_user_point(message_author_id)
            elif self.user_points[message_author_id].message_counts_towards_points():
                logger.info("user in user_points")
                alert_user = await self.user_points[message_author_id].increment_points()
                logger.info(f"alert_user={alert_user}")
                if alert_user:
                    await message.channel.send(
                        f"<@{message_author_id}> is now **level {self.user_points[message_author_id].level_number}**!"
                    )

    @commands.command()
    async def set_level_name(self, ctx, level_number: int, new_role_name: str):
        """

        :param ctx:
        :param level_number: example: 1
        :param new_role_name: example: Hello World
        :return:
        """
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...")
            return
        capitalized_new_role_name = new_role_name[0].upper() + new_role_name[1:]
        existing_xp_level_with_specified_role_name = [
            level for level in self.levels.values() if level.role_name == capitalized_new_role_name
        ]
        if len(existing_xp_level_with_specified_role_name) > 0:
            await ctx.send(
                f"role {capitalized_new_role_name} is already in use by level "
                f"{existing_xp_level_with_specified_role_name[0].number}"
            )
            return
        if level_number not in self.levels:
            current_levels = sorted([level.number for level in self.levels.values() if level.role_id is None])
            current_levels = [f"{level}" for level in current_levels]

            current_levels = ", ".join(current_levels)
            await ctx.send(
                f"you specified an incorrect level, the only levels available for setting their names "
                f"are :{current_levels}"
            )
            return
        if self.levels[level_number].role_id is None:
            # level does not yet have a role associated with it
            role = discord.utils.get(self.bot.guilds[0].roles, name=capitalized_new_role_name)
            await self.levels[level_number].set_level_name(capitalized_new_role_name, role.id)
            self.levels_have_been_changed = True
            await ctx.send(
                f"created role {capitalized_new_role_name} for level {level_number}. "
                f"Will take about 24 hours to apply role to the right people.\n\n"
                f"Don't forget to correct the role position"
            )

        else:
            role = ctx.guild.get_role(self.levels[level_number].role_id)
            if role is None:
                # the role id associated with the XP level doesn't seem to actually exist
                role = discord.utils.get(self.bot.guilds[0].roles, name=capitalized_new_role_name)
                await self.levels[level_number].set_level_name(capitalized_new_role_name, role.id)
                self.levels_have_been_changed = True
                await ctx.send(
                    f"created role {capitalized_new_role_name} for level {level_number}. "
                    f"Will take about 24 hours to apply role to the right people.\n\n"
                    f"Don't forget to correct the role position"
                )
            else:
                old_name = role.name
                await role.edit(name=capitalized_new_role_name)
                await self.levels[level_number].rename_level_name(capitalized_new_role_name)
                await ctx.send(f"renamed role {old_name} to {capitalized_new_role_name} for level {level_number}")

    @commands.command()
    async def remove_level_name(self, ctx, level_number: int):
        """

        :param ctx:
        :param level_number:
        :return:
        """
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...")
            return
        if self.levels[level_number].role_id is None:
            await ctx.send(f"level {level_number} does not have a role associated with it")
            return
        role = ctx.guild.get_role(self.levels[level_number].role_id)
        if role is not None:
            await role.delete()
        role_name = self.levels[level_number].role_name
        await self.levels[level_number].remove_role()
        self.levels_have_been_changed = True
        await ctx.send(f"role {role_name} has been removed")

    @commands.command()
    async def rank(self, ctx):
        """

        :param ctx:
        :return:
        """
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...")
            return
        message_author = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        message_author_id = message_author.id
        if message_author_id not in self.user_points:
            await ctx.send("specified user is not being tracked")
            return
        xp_required_to_level_up = await self.user_points[message_author_id].get_xp_needed_to_level_up_to_next_level()

        description = f"""
        {self.user_points[message_author_id].level_up_specific_points} / {xp_required_to_level_up} XP

        Total Messages: {self.user_points[message_author_id].message_count}

        """

        e_obj = await embed(
            ctx,
            avatar=message_author.avatar_url,
            author=message_author.name,
            title=f"{message_author.name}'s Stat Card",
            content=[
                (
                    f"Rank # {await self.user_points[message_author_id].get_rank()}",
                    f"Level # {self.user_points[message_author_id].level_number}")
            ],
            description=description
        )
        if e_obj is not None:
            await ctx.send(embed=e_obj)
