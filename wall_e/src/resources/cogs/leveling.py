import asyncio
import json
import logging

import discord
import requests
from discord.ext import commands

from WalleModels.models import Level, UserPoint
from resources.utilities.embed import embed
from resources.utilities.paginate import paginate_embed

logger = logging.getLogger('wall_e')


class Leveling(commands.Cog):

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
        self.council_channel = None
        self.bot.loop.create_task(self.load_data_from_mee6_endpoint_and_json())
        # self.bot.loop.create_task(self.create_council_channel())
        # self.bot.loop.create_task(self.ensure_roles_exist_and_have_right_users())

    async def load_data_from_mee6_endpoint_and_json(self):
        await self.bot.wait_until_ready()
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading XP data")
        if not await Level.level_points_have_been_imported():
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading levels into DB and dict")
            with open('resources/mee6_levels/levels.json') as f:
                self.levels = {
                    int(level_number): await Level.create_level(
                        int(level_number),
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
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading UserPoints into DB and dict")
            page = 0
            all_users_loaded = False
            while not all_users_loaded:
                r = requests.get(
                    f"https://mee6.xyz/api/plugins/levels/leaderboard/228761314644852736?page={page}&limit=1000",
                    headers={
                        'Authorization': self.config.get_config_value('basic_config', 'MEE6_AUTHORIZATION')
                    }
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
            logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] loading UserPoints from DB into dict")
            self.user_points = await UserPoint.load_to_dict()
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] UserPoints loaded in DB and dict")
        logger.info("[Mee6 load_data_from_mee6_endpoint_and_json()] XP data loaded")
        self.database_and_dict_populated = True

    async def create_council_channel(self):
        await self.bot.wait_until_ready()
        council_channel_id = None
        # determines the channel to send the XP messages on to the Moderators
        try:
            council_channel_name = 'council'
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'PRODUCTION':
                logger.info(
                    "[Mee6 create_council_channel()] environment is "
                    f"=[{self.config.get_config_value('basic_config', 'ENVIRONMENT')}]"
                )
                council_chan = discord.utils.get(self.bot.guilds[0].channels, name=council_channel_name)
                if council_chan is None:
                    logger.info("[Mee6 create_council_channel()] council channel does not exist in PRODUCTION.")
                    council_chan = await self.bot.guilds[0].create_text_channel(council_channel_name)
                    council_channel_id = council_chan.id
                    if council_channel_id is None:
                        logger.info("[Mee6 create_council_channel()] the channel designated for council messages "
                                    f"[{council_channel_name}] in PRODUCTION does not exist and I was"
                                    f" unable to create "
                                    "it, exiting now....")
                        exit(1)
                    logger.info("[Mee6 create_council_channel()] variable "
                                f"\"reminder_channel_id\" is set to \"{council_channel_id}\"")
                else:
                    logger.info(
                        "[Mee6 create_council_channel()] council channel exists in PRODUCTION and was detected.")
                    council_channel_id = council_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
                logger.info(
                    "[Mee6 create_council_channel()] branch is "
                    f"=[{self.config.get_config_value('basic_config', 'BRANCH_NAME')}]"
                )
                council_chan = discord.utils.get(
                    self.bot.guilds[0].channels,
                    name=f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_council"
                )
                if council_chan is None:
                    council_chan = await self.bot.guilds[0].create_text_channel(
                        f"{self.config.get_config_value('basic_config', 'BRANCH_NAME')}_council"
                    )
                    council_channel_id = council_chan.id
                    if council_channel_id is None:
                        logger.info(
                            "[Mee6 create_council_channel()] the channel designated for council messages "
                            f"[{self.config.get_config_value('basic_config', 'BRANCH_NAME')}_council] "
                            f"in {self.config.get_config_value('basic_config', 'BRANCH_NAME')} "
                            "does not exist and I was unable to create it, exiting now...."
                        )
                        exit(1)
                    logger.info("[Mee6 create_council_channel()] variable "
                                f"\"reminder_channel_id\" is set to \"{council_channel_id}\"")
                else:
                    logger.info(
                        f"[Mee6 create_council_channel()] council channel exists in "
                        f"{self.config.get_config_value('basic_config', 'BRANCH_NAME')} and was "
                        "detected."
                    )
                    council_channel_id = council_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
                council_channel_name = 'council'
                logger.info(
                    "[Mee6 create_council_channel()] environment is "
                    f"=[{self.config.get_config_value('basic_config', 'ENVIRONMENT')}]"
                )
                council_chan = discord.utils.get(self.bot.guilds[0].channels, name=council_channel_name)
                if council_chan is None:
                    logger.info("[Remindes create_council_channel()] council channel does not exist in local dev.")
                    council_chan = await self.bot.guilds[0].create_text_channel(council_channel_name)
                    council_channel_id = council_chan.id
                    if council_channel_id is None:
                        logger.info("[Mee6 create_council_channel()] the channel designated for council messages "
                                    f"[{council_channel_name}] in local dev does not exist and "
                                    f"I was unable to create it "
                                    "it, exiting now.....")
                        exit(1)
                    logger.info("[Mee6 create_council_channel()] variables "
                                f"\"reminder_channel_id\" is set to \"{council_channel_id}\"")
                else:
                    logger.info(
                        "[Mee6 create_council_channel()] council channel exists in local dev and was detected."
                    )
                    council_channel_id = council_chan.id
        except Exception as e:
            logger.error("[Mee6 create_council_channel()] encountered following exception when connecting to council "
                         f"channel\n{e}")
        self.council_channel = self.bot.get_channel(council_channel_id)  # channel ID goes here

    async def ensure_roles_exist_and_have_right_users(self):
        while not self.database_and_dict_populated:
            await asyncio.sleep(5)
        while True:
            if self.levels_have_been_changed:
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] updating user and roles for XP system"
                )
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
                    logger.info(
                        "[Mee6 ensure_roles_exist_and_have_right_users()]"
                        f" Moderators have been informed that {len(xp_roles_that_are_missing)}"
                        f" XP roles do not exist "
                    )
                members = await self.bot.guilds[0].fetch_members().flatten()

                # sorts the members in ascending order by their total cls
                members_with_points = [member for member in members if member.id in self.user_points]
                members_with_points.sort(key=lambda member: self.user_points[member.id].points)

                role_index = 0
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensuring that members with XP points"
                    " have the right XP roles"
                )
                for member_with_point in members_with_points:
                    while (
                            self.user_points[member_with_point.id].points >=
                            levels_with_a_role[role_index + 1].total_points_required
                    ):
                        role_index += 1
                    await member_with_point.remove_roles(*guild_roles[role_index:])
                    await member_with_point.add_roles(*guild_roles[:role_index])
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensured that the members with XP points"
                    " have the right XP roles")

                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensuring that members without XP points"
                    " don't have any XP roles "
                )
                for member_without_points in [member for member in members if member.id not in self.user_points]:
                    await member_without_points.remove_roles(*guild_roles)
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] ensured that members without XP points"
                    " don't have any XP roles "
                )
                self.levels_have_been_changed = False
                self.xp_system_ready = True
                logger.info(
                    "[Mee6 ensure_roles_exist_and_have_right_users()] users and role are now updated for XP system"
                )
            await asyncio.sleep(86400)

    @commands.Cog.listener(name='on_message')
    async def on_message(self, message):
        if not message.author.bot:
            if not self.xp_system_ready:
                return
            message_author_id = message.author.id
            logger.info(f"[Mee6 ensure_roles_exist_and_have_right_users()] detected message from {message_author_id}")
            if message_author_id not in self.user_points:
                logger.info(
                    f"[Mee6 ensure_roles_exist_and_have_right_users()] could not detect author {message_author_id} "
                    "in the user_points dict"
                )
                self.user_points[message_author_id] = await UserPoint.create_user_point(message_author_id)
            if await self.user_points[message_author_id].increment_points():
                logger.info(
                    f"[Mee6 ensure_roles_exist_and_have_right_users()] increased points for {message_author_id} "
                    " and alerting them that they are in a new level"
                )
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
        logger.info(
            f"[Mee6 set_level_name()] received request to set name for level {level_number} to {new_role_name}"
        )
        existing_xp_level_with_specified_role_name = [
            level for level in self.levels.values() if level.role_name == new_role_name
        ]
        logger.info(
            f"[Mee6 set_level_name()] len(existing_xp_level_with_specified_role_name)="
            f"{len(existing_xp_level_with_specified_role_name)}"
        )
        if len(existing_xp_level_with_specified_role_name) > 0:
            await ctx.send(
                f"role {new_role_name} is already in use by level "
                f"{existing_xp_level_with_specified_role_name[0].number}"
            )
            return
        if level_number not in list(self.levels.keys()):
            logger.info(f"[Mee6 set_level_name()] {level_number} is not valid")
            current_levels = sorted([level.number for level in self.levels.values() if level.role_id is None])
            current_levels = [f"{level}" for level in current_levels]

            current_levels = ", ".join(current_levels)
            await ctx.send(
                f"you specified an incorrect level, the only levels available for setting their names "
                f"are :{current_levels}"
            )
            return
        if self.levels[level_number].role_id is None:
            logger.info(f"[Mee6 set_level_name()] no role_id detected for level {level_number}")
            # level does not yet have a role associated with it
            role = discord.utils.get(self.bot.guilds[0].roles, name=new_role_name)
            if role is None:
                logger.info(
                    f"[Mee6 set_level_name()] could not find the role {new_role_name}"
                    f" to associate with {level_number}"
                )
                await ctx.send(f"could not find role {new_role_name}. ")
            else:
                logger.info(
                    f"[Mee6 set_level_name()] associating level {level_number} with role {new_role_name}"
                )
                await self.levels[level_number].set_level_name(new_role_name, role.id)
                self.levels_have_been_changed = True
                await ctx.send(
                    f"assigned role {new_role_name} for level {level_number}. "
                    f"Will take about 24 hours to apply role to the right people.\n\n"
                    f"Don't forget to correct the role position"
                )

        else:
            logger.info(f"[Mee6 set_level_name()] role_id detected for level {level_number}")
            role = ctx.guild.get_role(self.levels[level_number].role_id)
            if role is None:
                logger.info(f"[Mee6 set_level_name()] detected role_id detected for level {level_number} is invalid")
                # the XP level is getting a new role since the role it was associated with was an error
                role = discord.utils.get(self.bot.guilds[0].roles, name=new_role_name)
                if role is None:
                    await ctx.send(f"could not find role {new_role_name}. ")
                else:
                    await self.levels[level_number].set_level_name(new_role_name, role.id)
                    logger.info(
                        f"[Mee6 set_level_name()] set flag to associate level {level_number} with role {role.name}"
                    )
                    self.levels_have_been_changed = True
                    await ctx.send(
                        f"Associated role {new_role_name} for level {level_number}. "
                        f"Will take about 24 hours to apply role to the right people.\n\n"
                        f"Don't forget to correct the role position"
                    )
            else:
                old_name = role.name
                logger.info(
                    f"[Mee6 set_level_name()] renaming role {old_name} to {new_role_name} for level {level_number}"
                )
                await role.edit(name=new_role_name)
                await self.levels[level_number].rename_level_name(new_role_name)
                await ctx.send(f"renamed role {old_name} to {new_role_name} for level {level_number}")

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
            logger.info(
                f"[Mee6 remove_level_name()] resetting role info to Null for level {level_number}"
            )
            await self.levels[level_number].remove_role()
            await ctx.send(f"level {level_number} does not have an existing role associated with it")
            return
        role_name = self.levels[level_number].role_name
        await self.levels[level_number].remove_role()
        logger.info(
            f"[Mee6 remove_level_name()] resetting role info to Null for level {level_number}"
        )
        self.levels_have_been_changed = True
        await ctx.send(
            f"role {role_name} was disassociated from level {level_number}\n\n"
            f"Don't forget to delete the role"
        )

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

    @commands.command()
    async def levels(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...")
            return
        levels_with_a_role = [level for level in self.levels.values() if level.role_name is not None]
        levels_with_a_role.sort(key=lambda level: level.number)

        levels_with_a_valid_role = []
        levels_with_an_invalid_role = []
        for level_with_role in levels_with_a_role:
            role = discord.utils.get(self.bot.guilds[0].roles, name=level_with_role.role_name)
            if role is not None:
                levels_with_a_valid_role.append(level_with_role)
            else:
                levels_with_an_invalid_role.append(level_with_role)

        descriptions_to_embed = []
        description_to_embed = "\nLevel Number - Level Role\n"
        for (index, level) in enumerate(levels_with_a_valid_role):
            if index % 10 == 0 and index > 0:
                descriptions_to_embed.append(description_to_embed)
                description_to_embed = "\nLevel Number - Level Role\n"
            description_to_embed += f"{level.number} - {level.role_name}\n"
        if description_to_embed != "\nLevel Number - Level Role\n":
            descriptions_to_embed.append(description_to_embed)

        description_to_embed = "\nLevel Number - Invalid Level Role\n"
        for (index, level) in enumerate(levels_with_an_invalid_role):
            if index % 10 == 0 and index > 0:
                descriptions_to_embed.append(description_to_embed)
                description_to_embed = "\nLevel Number - Invalid Level Role\n"
            description_to_embed += f"{level.number} - {level.role_name}\n"
        if description_to_embed != "\nLevel Number - Invalid Level Role\n":
            descriptions_to_embed.append(description_to_embed)

        await paginate_embed(self.bot, ctx, self.config, descriptions_to_embed, title="Levels")
