import asyncio
import datetime
import math
import random
import time

import discord
import pytz
from aiohttp import ServerDisconnectedError, ClientOSError, ClientPayloadError
from discord import NotFound, app_commands, Guild
from discord.errors import DiscordException
from discord.ext import commands, tasks

from utilities.embed import embed, COLOUR_MAPPING, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.global_vars import bot, wall_e_config
from utilities.paginate import paginate_embed
from utilities.setup_logger import Loggers, log_exception
from wall_e_models.models import Level, UserPoint, UpdatedUser, ProfileBucketInProgress


class Leveling(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Leveling")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.warn_log_file_absolute_path = log_info[2]
        self.error_log_file_absolute_path = log_info[3]
        self.logger.info("[Leveling __init__()] initializing Leveling")

        process_lurkers_log_info = Loggers.get_logger(logger_name="Leveling_process_lurkers")
        self.process_lurkers_logger = process_lurkers_log_info[0]
        self.process_lurkers_debug_log_file_absolute_path = process_lurkers_log_info[1]

        update_outdated_profile_pics_log_info = Loggers.get_logger(
            logger_name="Leveling_update_outdated_profile_pics"
        )
        self.process_outdated_profile_pics_in_progress = False
        self.update_outdated_profile_pics_logger = update_outdated_profile_pics_log_info[0]
        self.update_outdated_profile_pics_debug_log_file_absolute_path = update_outdated_profile_pics_log_info[1]
        self.update_outdated_profile_pics_warn_log_file_absolute_path = update_outdated_profile_pics_log_info[2]
        self.update_outdated_profile_pics_error_log_file_absolute_path = update_outdated_profile_pics_log_info[3]

        self.levels_have_been_changed = False
        self.guild: Guild | None = None
        self.user_points = None
        self.levels = None
        self.xp_system_ready = False
        self.council_channel = None
        self.levelling_website_avatar_channel = None
        self.bucket_update_in_progress = False
        self.NUMBER_OF_UPDATE_ATTEMPTS_PER_USER = 15
        self.MAX_RETRIES_FOR_FETCHING_USER = 5
        self.MAX_USER_UPDATE_CONCURRENT_ATTEMPTS = 30
        self.ensure_xp_roles_exist_and_have_right_users.start()
        self.process_leveling_profile_data_for_lurkers.start()
        self.process_outdated_profile_pics.start()
        self.process_leveling_profile_data_for_active_users.start()

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path,
            "leveling_debug"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_warn_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.warn_log_file_absolute_path,
            "leveling_warn"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path,
            "leveling_error"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_process_lurkers_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config, self.process_lurkers_debug_log_file_absolute_path,
            "process_lurkers"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_outdated_profile_pics_debug_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config,
            self.update_outdated_profile_pics_debug_log_file_absolute_path,
            "update_outdated_profile_pics"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_outdated_profile_pics_warn_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config,
            self.update_outdated_profile_pics_warn_log_file_absolute_path,
            "update_outdated_profile_pics_warn"
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_outdated_profile_pics_error_logs(self):
        while self.guild is None:
            await asyncio.sleep(2)
        await start_file_uploading(
            self.logger, self.guild, bot, wall_e_config,
            self.update_outdated_profile_pics_error_log_file_absolute_path,
            "update_outdated_profile_pics_error"
        )

    @commands.Cog.listener(name="on_ready")
    async def updating_database_and_cache(self):
        """
        Loads the current level info and user points into the self.levels and self.user_points dict respectively
        for quicker read access
        :return:
        """
        self.logger.info("[Leveling updating_database_and_cache()] loading UserPoints and level into DB and cache")
        level_names = {
            0: "Hello World",
            5: "Missing Semicolon",
            10: "Manual Tester",
            15: "Javascript Programmer",
            20: "Syntax Error",
            25: "Git Gud",
            30: "Full Stack Developer",
            35: "Assembly Programmer",
            40: "Segmentation Fault",
            45: "Vim User",
            50: "Kernel",
            55: "Stallman Follower",
            60: "Forkbomb",
            65: "Human Compiler",
            70: "Gentoo Installer",
            75: "HolyC",
            80: "CD level80",
            85: "THE 85",
            90: "THE 90",
            95: "THE 95"
        }
        if await Level.all_level_have_been_imported_into_database():
            self.logger.debug("[Leveling updating_database_and_cache()] loading levels from DB into cache")
            self.levels = await Level.load_to_cache()
            self.logger.debug("[Leveling updating_database_and_cache()] levels loaded from DB into cache")
        else:
            self.logger.debug("[Leveling updating_database_and_cache()] loading levels into DB and cache")
            self.levels = {}
            total_xp_required = 0
            for level in range(0, 101):
                # pulled from
                # https://web.archive.org/web/20230315031903/https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md
                level_up_required = 5 * int(math.pow(level, 2)) + (50 * level) + 100
                self.levels[level] = await Level.create_level(
                    level, total_xp_required, level_up_required, role_name=level_names.get(level, None)
                )
                total_xp_required += level_up_required
            self.logger.debug("[Leveling updating_database_and_cache()] levels loaded into DB and cache")
        self.logger.debug("[Leveling updating_database_and_cache()] loading UserPoints into cache")
        await UserPoint.reset_attempts_and_process_status(self.logger)
        self.user_points = await UserPoint.load_to_cache()
        self.logger.debug("[Leveling updating_database_and_cache()] UserPoints loaded into cache")
        self.logger.debug("[Leveling updating_database_and_cache()] XP system ready")
        self.xp_system_ready = True

    @commands.Cog.listener(name="on_ready")
    async def create_council_channel(self):
        """
        Gets the council_channel that will be used or any mod-relevant messages for Leveling cog class
        :return:
        """
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info("[Leveling create_council_channel()] acquiring text channel for council.")
        council_channel_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            "leveling"
        )
        self.council_channel = discord.utils.get(
            self.guild.channels if self.guild else None, id=council_channel_id
        )
        self.logger.debug(
            f"[Leveling create_council_channel()] text channel {self.council_channel} acquired."
        )

    @commands.Cog.listener(name="on_ready")
    async def get_leveling_avatar_channel(self):
        """
        Gets the leveling_avatar_images_channel that will be used to store the user profile pics used by the
        leveling website
        :return:
        """
        while self.guild is None:
            await asyncio.sleep(2)
        self.logger.info(
            "[Leveling get_leveling_avatar_channel()] acquiring text channel for the avatars used on the leveling"
            " website."
        )
        leveling_website_avatar_images_channel_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            'leveling_website_avatar_images'
        )
        self.levelling_website_avatar_channel: discord.TextChannel = discord.utils.get(
            self.guild.channels if self.guild else None, id=leveling_website_avatar_images_channel_id
        )
        self.logger.debug(
            f"[Leveling get_leveling_avatar_channel()] bot channel {self.levelling_website_avatar_channel} acquired."
        )

    @commands.Cog.listener(name='on_message')
    async def on_message(self, message):
        """
        called whenever a new message is sent on the guild to potentially increase the user points for
         the message's author
        :param message: the message that was sent that tripped the function call
        :return:
        """
        while self.guild is None or self.levelling_website_avatar_channel is None:
            await asyncio.sleep(2)
        if not message.author.bot:
            if not self.xp_system_ready:
                return
            message_author_id = message.author.id
            if message_author_id not in self.user_points:
                self.logger.debug(
                    f"[Leveling on_message()] could not detect author {message.author}({message_author_id}) "
                    "in the user_points dict"
                )
                self.user_points[message_author_id] = await UserPoint.create_user_point(message_author_id)
            if await self.user_points[message_author_id].increment_points():
                self.logger.debug(
                    f"[Leveling on_message()] increased points for {message.author}({message_author_id}) "
                    f" and alerting them that they are in a new level in channel {message.channel}"
                )
                level = self.levels[self.user_points[message_author_id].level_number]
                if level.role_id is not None:
                    role = message.guild.get_role(level.role_id)
                    if role is not None:
                        self.logger.debug(
                            f"[Leveling on_message()] the new level {level.number} "
                            f" for user {message.author}({message_author_id}) has the role {role} "
                            f"associated with it. Assigning to user"
                        )
                        await message.author.add_roles(role)
                    else:
                        self.logger.debug(
                            f"[Leveling on_message()] the new level {level.number} "
                            f" for user {message.author}({message_author_id}) has an invalid role {role} associated "
                            f"with it. Alerting the council to this "
                        )
                        await self.council_channel.send(
                            "The XP role could not be found. Please call `.remove_level_name <level_number>` "
                            "to confirm that you want the XP roles deleted or re-create the roles:\n\n"
                            "Role Name - Linked XP Level\n"
                            f"{level.role_name} - {level.number}"
                        )

                await message.channel.send(
                    f"<@{message_author_id}> is now **level {level.number}**!"
                )
                self.logger.debug(f"[Leveling on_message()] message sent to {message.author}({message_author_id})")

    @tasks.loop(time=datetime.time(hour=5, tzinfo=pytz.timezone('Canada/Pacific')))
    async def ensure_xp_roles_exist_and_have_right_users(self):
        """
        Runs once a day to detect if the levels have been changed and therefore the user's level for their points
        need to be updated
        :return:
        """
        if self.guild is None or not self.xp_system_ready or self.council_channel is None:
            return
        if self.levels_have_been_changed:
            self.logger.info(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] updating user and roles for XP system"
            )
            levels_with_a_role = [level for level in self.levels.values() if level.role_name is not None]
            levels_with_a_role.sort(key=lambda level: level.number)
            # ordering level roles in an ascending order
            self.logger.debug(
                f"[Leveling ensure_xp_roles_exist_and_have_right_users()] ensuring that all {len(levels_with_a_role)}"
                f" XP roles exist"
            )
            guild_roles = await self._get_level_roles(levels_with_a_role)
            members = await self.guild.fetch_members().flatten()

            # sorts the members in ascending order by their total
            members_with_points = [member for member in members if member.id in self.user_points]
            members_with_points.sort(key=lambda member: self.user_points[member.id].points)

            self.logger.debug(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] ensuring that members with XP points"
                " have the right XP roles"
            )
            await self._set_xp_roles_for_members_with_xp_points(members_with_points, levels_with_a_role, guild_roles)

            self.logger.debug(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] ensured that the members with XP points"
                " have the right XP roles"
            )

            self.logger.debug(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] ensuring that members without XP points"
                " don't have any XP roles "
            )

            await self._set_xp_roles_for_members_with_no_xp_points(members, guild_roles)

            self.logger.debug(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] ensured that members without XP points"
                " don't have any XP roles "
            )
            self.levels_have_been_changed = False
            self.logger.debug(
                "[Leveling ensure_xp_roles_exist_and_have_right_users()] users and role are now updated for XP system"
            )

    async def _get_level_roles(self, levels_with_a_role):
        """
        gets a list of all the guild roles that are associated wth an XP level
        :param levels_with_a_role: a list of Level objects representing an XP level that have role associated with
         them
        :return: the list of guild roles
        """
        guild_roles = []
        xp_roles_that_are_missing = {}
        for level_with_role in levels_with_a_role:
            role = discord.utils.get(self.guild.roles, name=level_with_role.role_name)
            if role:
                guild_roles.append(role)
                level_with_role.role_id = role.id
                await level_with_role.async_save()
            else:
                xp_roles_that_are_missing[level_with_role.role_name] = level_with_role.number
        if len(xp_roles_that_are_missing) == 0:
            self.logger.debug(
                "[Leveling _get_level_roles()] all"
                f" {len(levels_with_a_role)} XP roles exist"
            )
        else:
            xp_roles_that_are_missing = [
                f"{role_name} - {role_number}"
                for role_name, role_number in xp_roles_that_are_missing.items()
            ]
            xp_roles_that_are_missing = "\n".join(xp_roles_that_are_missing)
            await self.council_channel.send(
                "The following XP roles could not be found. Please call "
                "`.remove_level_name <level_number>` to confirm that you want the XP roles deleted or "
                "re-create the roles:\n\nRole Name - Linked XP Level\n"
                f"{xp_roles_that_are_missing}"
            )
            self.logger.debug(
                "[Leveling _get_level_roles()]"
                f" Moderators have been informed that {len(xp_roles_that_are_missing)}"
                f" XP roles do not exist "
            )
        return guild_roles

    async def _set_xp_roles_for_members_with_xp_points(self, members_with_points, levels_with_a_role, guild_roles):
        """
        Adjusts what XP associated guild roles are associated with any members that have XP points

        :param members_with_points: a list of members with XP points
        :param levels_with_a_role: the list of XP levels that are associated with a guild role
        :param guild_roles: the list of guild roles associated with an XP level
        :return:
        """
        role_index = 0
        prev_number_of_members_fixed = number_of_members_fixed = 0
        prev_number_of_members_skipped = number_of_members_skipped = 0
        number_of_members = len(members_with_points)

        for member_with_point in members_with_points:
            def member_has_points_required_for_role(current_role_index):
                return (
                    len(levels_with_a_role) > (current_role_index + 1) and
                    self.user_points[member_with_point.id].points >=
                    levels_with_a_role[current_role_index + 1].total_points_required
                )

            while member_has_points_required_for_role(role_index):
                role_index += 1
            initial_time = time.perf_counter()
            latest_attempt_time = time.perf_counter()
            iteration = 0
            successful = False
            while (not successful) and ((latest_attempt_time - initial_time) <= 64):
                try:
                    await member_with_point.remove_roles(*guild_roles[role_index + 1:])
                    await member_with_point.add_roles(*guild_roles[:role_index + 1])
                    number_of_members_fixed += 1
                    successful = True
                except Exception as e:
                    self.logger.warn(
                        "[Leveling _set_xp_roles_for_members_with_xp_points()] encountered "
                        f"following error when fixing the roles for member {member_with_point} on iteration "
                        f"{iteration}.\n{e}"
                    )
                    await self.exponential_backoff_sleep(iteration)
                    latest_attempt_time = time.perf_counter()
                iteration += 1
            if not successful:
                number_of_members_skipped += 1
                log_exception(
                    self.logger,
                    f"[Leveling _set_xp_roles_for_members_with_xp_points()] "
                    f"tried to fix the"
                    f" permissions for member {member_with_point} {iteration} times, moving onto "
                    f"next member"
                )
            new_number_of_member_skipped_or_fixed = (
                    (
                        prev_number_of_members_skipped != number_of_members_skipped and
                        number_of_members_skipped % 10 == 0  # so that the output doesn't get spammed
                    ) or
                    (
                        prev_number_of_members_fixed != number_of_members_fixed and
                        number_of_members_fixed % 10 == 0  # so that the output doesn't get spammed
                    )
            )

            if new_number_of_member_skipped_or_fixed:
                prev_number_of_members_skipped = number_of_members_skipped
                prev_number_of_members_fixed = number_of_members_fixed
                self.logger.debug(
                    f"[Leveling _set_xp_roles_for_members_with_xp_points()] current_progress so far..."
                    f" number_of_members_fixed = {number_of_members_fixed}/{number_of_members} || "
                    f"number_of_members_skipped = {number_of_members_skipped}/{number_of_members}"
                )
            await asyncio.sleep(1)

    async def _set_xp_roles_for_members_with_no_xp_points(self, members, guild_roles):
        """
        Removes any guild roles from any members that don't have any XP points yet
        :param members: list of members with no XP points
        :param guild_roles: the list of guild roles associated with an XP level
        :return:
        """
        for member_without_points in [member for member in members if member.id not in self.user_points]:
            try:
                await member_without_points.remove_roles(*guild_roles)
            except Exception as e:
                log_exception(
                    self.logger,
                    "[Leveling _set_xp_roles_for_members_with_no_xp_points()] encountered following error when fixing"
                    " the roles for member {member_without_points}",
                    error=e
                )
            await asyncio.sleep(1)

    @commands.Cog.listener(name='on_member_join')
    async def assign_roles_on_member_join(self, member: discord.Member):
        """
        Set the necessary XP levels to the member that was joined in case they previously were in the guild
        :param member: the member whose join triggered the function call and may need their XP levels re-assigned
        :return:
        """
        while not self.xp_system_ready:
            await asyncio.sleep(2)
        if member.id not in self.user_points:
            return
        from extensions.ban import Ban
        if member.id in Ban.ban_list:
            return
        self.logger.info(
            f"[Leveling assign_roles_on_member_join()] ensuring a {member} with {self.user_points[member.id].points} "
            f"points wil get their roles back if they leave and re-join the guild"
        )

        levels_with_a_role = [
            level for level in self.levels.values()
            if level.role_name is not None and level.total_points_required <= self.user_points[member.id].points
        ]
        if len(levels_with_a_role) == 0:
            self.logger.debug(
                f"[Leveling assign_roles_on_member_join()] seems user {member} is entitled to no XP levels"
            )
            return
        self.logger.debug(
            f"[Leveling assign_roles_on_member_join()] seems user {member} is entitled to the following levels which"
            f" have a role: {levels_with_a_role}"
        )

        guild_roles = [
            member.guild.get_role(self.levels[level_with_role.number].role_id)
            for level_with_role in levels_with_a_role
        ]
        guild_roles = [guild_role for guild_role in guild_roles if guild_role]

        self.logger.debug(
            f"[Leveling assign_roles_on_member_join()] will get the {guild_roles} roles added back to {member}"
        )
        number_of_retries = 0
        success = False
        while number_of_retries < 5 and (success is False):
            try:
                number_of_retries += 1
                await member.add_roles(*guild_roles)
                success = True
            except Exception as e:
                self.logger.debug(
                    f"[Leveling assign_roles_on_member_join()] encountered following error when fixing the roles for "
                    f"member {member}, \n{type(e)}\n{e}"
                )
                if number_of_retries < 5:
                    self.logger.debug("[Leveling assign_roles_on_member_join()] will try again in one minute")
                    await asyncio.sleep(60)
        if success:
            self.logger.debug(f"[Leveling assign_roles_on_member_join()] XP roles fixed for user {member}")
        else:
            log_exception(
                self.logger,
                f"[Leveling assign_roles_on_member_join()] could not fix the XP roles for user {member}"
            )

    @tasks.loop(minutes=30)
    async def process_leveling_profile_data_for_lurkers(self):
        """
        Goes through all the UserPoint objects whose avatar CDN link has expired or who don't yet have a bucket number
        and ensure their information has been updated for the leveling website
        """
        not_ready_to_process_lurkers = (
                self.user_points is None or self.levelling_website_avatar_channel is None or self.guild is None or
                self.bucket_update_in_progress
        )
        self.process_lurkers_logger.debug(
            f"[Leveling process_leveling_profile_data_for_lurkers()] background task starting "
            f"self.user_points is None = {self.user_points is None} | self.levelling_website_avatar_channel is None "
            f"= {self.levelling_website_avatar_channel is None} | self.guild is None = {self.guild is None} | "
            f"self.bucket_update_in_progress = {self.bucket_update_in_progress} | not_ready_to_process_lurkers = "
            f"{not_ready_to_process_lurkers}"
        )
        if not_ready_to_process_lurkers:
            return
        self.process_lurkers_logger.debug(
            "[Leveling process_leveling_profile_data_for_lurkers()] background task proceeding"
        )

        await self._set_bucket_numbers(self.process_lurkers_logger)

        entry = await self._get_current_bucket_number()

        user_ids_to_update = await UserPoint.get_users_with_current_bucket_number(entry.bucket_number_completed)

        self.process_lurkers_logger.debug(
            f"[Leveling process_leveling_profile_data_for_lurkers()] {user_ids_to_update} "
            f"potential updates retrieved for bucket {entry.bucket_number_completed}"
        )
        await self._update_users_with_given_ids(self.process_lurkers_logger, user_ids_to_update)
        await ProfileBucketInProgress.async_save(entry)

    async def _set_bucket_numbers(self, logger):
        """
        Assigns a bucket_number to any new UserPoints that don't yet have one

        The logic is implemented by creating a dictionary with a bucket for each hour of the month with the lowest
         number of days so that this algorithm can also work on leap years.
         The idea is that each user will be set a certain hour of the month when it should be updated. And it will
          only be updated in that time ASSUMING that the user is a lurker who is not regularly sending messages.
           Because if the user is regular sending messages, chances are any changes in their profile will be caught
        by get_updated_user_logs
        :return:
        """
        user_points = [user_point for user_point in self.user_points.values() if user_point.bucket_number is None]
        if len(user_points) == 0:
            return

        if self.bucket_update_in_progress:
            return
        self.bucket_update_in_progress = True
        users_to_update = self._setup_bucket_number_for_new_users()

        logger.debug(
            f"[Leveling _set_bucket_numbers()] updating {len(users_to_update)} user_point objects' bucket_number"
        )
        await UserPoint.async_bulk_update(users_to_update, ["bucket_number"])
        logger.debug(
            "[Leveling _set_bucket_numbers()] null bucket_number has been updated"
        )
        self.bucket_update_in_progress = False
        logger.debug(
            f"[Leveling _set_bucket_numbers()] updated {len(users_to_update)} user_point objects' date_to_check"
        )

    def _setup_bucket_number_for_new_users(self) -> list:
        """
        :return: the users who need to have their bucket_number updated
        """
        date_buckets = self._initialize_bucket_with_number_of_current_users()
        users_to_update = []
        for user_id in self.user_points.keys():
            if self.user_points[user_id].bucket_number is None:
                lowest_bucket_number = self._get_bucket_number_with_lowest_number_of_users(date_buckets)
                date_buckets[lowest_bucket_number] += 1
                self.user_points[user_id].bucket_number = lowest_bucket_number
                users_to_update.append(self.user_points[user_id])
        return users_to_update

    def _initialize_bucket_with_number_of_current_users(self) -> dict:
        """
        :return: the bucket dict with the users that currently have a bucket_number attached
         already reflected on it
        """
        date_buckets = Leveling._initialize_blank_bucket()

        # populate the date_buckets values with the number of users that currently exist in those buckets
        for user_id in self.user_points.keys():
            if self.user_points[user_id].bucket_number is not None:
                date_buckets[self.user_points[user_id].bucket_number] += 1
        return date_buckets

    @staticmethod
    def _initialize_blank_bucket() -> dict:
        """
        :return: a blank bucket dict that has the slots necessary to determine when people should be divided into
         slots/buckets within a 2-week period
        """
        date_buckets = {}
        bucket_number = 1
        for day in range(1, 24):  # discord CDN links apparently expire after 1 day and need to be re-retrieved
            for minute in range(1, 2):  # decided to setup the buckets to be every half hour
                date_buckets[bucket_number] = 0
                bucket_number += 1
        return date_buckets

    @staticmethod
    def _get_bucket_number_with_lowest_number_of_users(data_buckets):
        """
        :param data_buckets:
        :return: the bucket_number which has the lowest number of users
        """
        low_load_bucket_number = None
        min_value = None
        for curr_bucket_number, number_of_user_to_checks in data_buckets.items():
            if min_value is None:
                low_load_bucket_number = curr_bucket_number
                min_value = number_of_user_to_checks
            elif min_value > number_of_user_to_checks:
                low_load_bucket_number = curr_bucket_number
                min_value = number_of_user_to_checks
        return low_load_bucket_number

    async def _get_current_bucket_number(self) -> ProfileBucketInProgress:
        """
        :return: the bucket_number to work on in the current iteration
        """
        entry = await ProfileBucketInProgress.retrieve_entry()
        if entry is None:
            entry = await ProfileBucketInProgress.create_entry()
        else:
            bucket_numbers = [
                user_point.bucket_number for user_point in self.user_points.values()
                if user_point.bucket_number is not None
            ]
            bucket_numbers.sort(key=lambda x: x, reverse=True)
            max_bucket_number = bucket_numbers[0]
            entry.bucket_number_completed += 1
            if entry.bucket_number_completed > max_bucket_number:
                entry.bucket_number_completed = 1
        return entry

    async def _update_users_with_given_ids(self, logger, updated_user_ids):
        """
        iterates through the given list of user_ids and updates them
        :param updated_user_ids:
        :return:
        """
        total_number_of_updates_needed = len(updated_user_ids)
        for index, user_id in enumerate(updated_user_ids):
            if self.user_points[user_id].being_processed:
                if self.user_points[user_id].concurrent_attempts > self.MAX_USER_UPDATE_CONCURRENT_ATTEMPTS:
                    self.user_points[user_id].concurrent_attempts = 0
                else:
                    self.user_points[user_id].concurrent_attempts += 1
                    logger.info(
                        f"[Leveling _update_users_with_given_ids()] skipping user with ID {user_id} who is apparently"
                        " already being processed"
                    )
                    continue
            self.user_points[user_id].being_processed = True
            user_processed = False
            logger.debug(
                f"[Leveling _update_users_with_given_ids()] attempt "
                f"{self.user_points[user_id].leveling_update_attempt} to get updated user_point profile data for "
                f"member {user_id} {index + 1}/{total_number_of_updates_needed} "
            )
            member = await self.get_user_with_retry(logger, user_id)
            error = None
            if member:
                while (
                        not user_processed and
                        self.user_points[user_id].leveling_update_attempt < self.NUMBER_OF_UPDATE_ATTEMPTS_PER_USER
                ):
                    self.user_points[user_id].leveling_update_attempt += 1
                    await self.exponential_backoff_sleep(self.user_points[user_id].leveling_update_attempt)
                    try:
                        user_updated, user_processed = await self._update_member_profile_data(
                            logger, member, user_id, index, total_number_of_updates_needed
                        )
                    except Exception as e:
                        error = e
                        logger.warning(
                            "[Leveling _update_users_with_given_ids()] experiencing error while trying to"
                            f" update user_point profile data for member {user_id} {index + 1}/"
                            f"{total_number_of_updates_needed} "
                        )
                if not user_processed:
                    log_exception(
                        logger,
                        f"[Leveling _update_users_with_given_ids()] got the following error when updating a"
                        f" discord user {user_id}",
                        error=error
                    )
            self.user_points[user_id].being_processed = False

    @tasks.loop(seconds=2)
    async def process_leveling_profile_data_for_active_users(self):
        """
        Goes through all the UserPoint objects that have been marked indicated their profile has been updated
         and needs to have wall_e's database updated for the leveling website
        :return:
        """
        if self.user_points is None or self.levelling_website_avatar_channel is None or self.guild is None:
            return
        updated_user_logs = await UpdatedUser.get_updated_user_logs()
        total_number_of_updates_needed = len(updated_user_logs)
        for index, update_user in enumerate(updated_user_logs):
            updated_user_id = update_user[1]
            if self.user_points[updated_user_id].being_processed:
                if self.user_points[updated_user_id].concurrent_attempts > self.MAX_USER_UPDATE_CONCURRENT_ATTEMPTS:
                    self.user_points[updated_user_id].concurrent_attempts = 0
                else:
                    self.user_points[updated_user_id].concurrent_attempts += 1
                    self.logger.info(
                        f"[Leveling process_leveling_profile_data_for_active_users()] skipping user with ID"
                        f" {updated_user_id} who is apparently already being processed"
                    )
                    continue
            self.user_points[updated_user_id].being_processed = True
            updated_user_log_id = update_user[0]  # noqa: F841
            user_processed = False
            member = await self.get_user_with_retry(self.logger, updated_user_id)
            error = None
            if member:
                while (
                        not user_processed and
                        self.user_points[updated_user_id].leveling_update_attempt <
                        self.NUMBER_OF_UPDATE_ATTEMPTS_PER_USER
                ):
                    self.user_points[updated_user_id].leveling_update_attempt += 1
                    self.logger.debug(
                        f"[Leveling process_leveling_profile_data_for_active_users()] attempt "
                        f"{self.user_points[updated_user_id].leveling_update_attempt} to get data for user with "
                        f"UpdatedUser id [{updated_user_log_id}] with id {updated_user_id} "
                        f"{index + 1}/{total_number_of_updates_needed} "
                    )
                    await self.exponential_backoff_sleep(self.user_points[updated_user_id].leveling_update_attempt)
                    try:
                        # cannot call _update_users_with_given_ids like process_outdated_profile_pics and
                        # process_leveling_profile_data_for_lurkers because this task needs to be able to specify a
                        # updated_user_log_id that will be deleted update_leveling_profile_info when the user is
                        # processed
                        _, user_processed = await self._update_member_profile_data(
                            self.logger, member, updated_user_id, index, total_number_of_updates_needed,
                            updated_user_log_id=updated_user_log_id
                        )
                    except Exception as e:
                        error = e
                        self.logger.warning(
                            "[Leveling process_leveling_profile_data_for_active_users()] experiencing error while"
                            f" trying to update user_point profile data for member {member} {index + 1}/"
                            f"{total_number_of_updates_needed} "
                        )
                if not user_processed:
                    log_exception(
                        self.logger,
                        f"[Leveling process_leveling_profile_data_for_active_users()] got the following"
                        f" error when updating a discord user {updated_user_id}",
                        error=error
                    )
            self.user_points[updated_user_id].being_processed = False

    async def get_user_with_retry(self, logger, user_id):
        user = None
        error = None
        for attempt in range(self.MAX_RETRIES_FOR_FETCHING_USER):
            try:
                user = await self.guild.fetch_member(user_id)
            except NotFound as e:
                error = e
                try:
                    user = await bot.fetch_user(user_id)
                except (DiscordException, ServerDisconnectedError, ClientOSError, ClientPayloadError) as e:
                    error = e
                    await self.exponential_backoff_sleep(attempt)
            except (DiscordException, ServerDisconnectedError, ClientOSError, ClientPayloadError) as e:
                error = e
                await self.exponential_backoff_sleep(attempt)
        if user is None:
            log_exception(
                logger,
                f"[Leveling get_user_with_retry()] got the following error when fetching discord user {user_id}",
                error=error
            )
        return user

    async def exponential_backoff_sleep(self, attempt):
        random_number_milliseconds = random.randint(0, 1000) / 1000
        sleep_seconds = math.pow(
            2, attempt + random_number_milliseconds
        )
        await asyncio.sleep(sleep_seconds)

    @tasks.loop(seconds=5)
    async def process_outdated_profile_pics(self):
        if self.guild is None or self.user_points is None:
            return
        if self.process_outdated_profile_pics_in_progress:
            return
        self.process_outdated_profile_pics_in_progress = True
        user_ids_to_update = await UserPoint.get_users_with_expired_images()
        number_of_users_to_update = len(user_ids_to_update)
        if number_of_users_to_update == 0:
            self.process_outdated_profile_pics_in_progress = False
            return
        self.update_outdated_profile_pics_logger.debug(
            f"[Leveling process_outdated_profile_pics()] {number_of_users_to_update} users with outdated CDN links"
            f" to update"
        )
        await self._update_users_with_given_ids(self.update_outdated_profile_pics_logger, user_ids_to_update)
        self.process_outdated_profile_pics_in_progress = False

    async def _update_member_profile_data(self, logger, member, updated_user_id, index,
                                          total_number_of_updates_needed, updated_user_log_id=None):
        """
        Attempts to determine if the member's leveling data in the database can be updated and if not, record any of
         the errors detected as a result

        :param member: the member who's leveling data to extract to the database
        :param updated_user_id: the ID for the user whose leveling data is being updated, pulled from the database
        :param index: index of member amongst the current iteration that is being updated
        :param total_number_of_updates_needed: number of members the code is attempting to update within the
         current loop
        :param updated_user_log_id: the ID of the UpdatedUser record to delete if this function was called as a
         result of member_update_listener's recording any detected changed in UpdatedUser
        :return: True if member was successfully processed
        """
        user_updated = False
        user_processed = False
        try:
            expiry_date = (
                self.user_points[member.id].discord_avatar_link_expiry_date.pst
                if self.user_points[member.id].discord_avatar_link_expiry_date else None
            )
            logger.debug(
                f"[Leveling _update_member_profile_data()] "
                f"attempt {self.user_points[member.id].leveling_update_attempt} to update the member profile "
                f"data in the database for member {member} with id [{member.id}], "
                f"updated_user_log_id = {updated_user_log_id}, expiry_date of [{expiry_date}] and a CDN link of "
                f"<{self.user_points[member.id].leveling_message_avatar_url}> "
                f"{index + 1}/{total_number_of_updates_needed}"
            )
            # leveling_update_attempt is reset to 0 in update_leveling_profile_info if member is successfully
            # updated THIS time
            user_updated, user_processed = await self.user_points[member.id].update_leveling_profile_info(
                logger, self.guild.id, member, self.levelling_website_avatar_channel,
                updated_user_log_id=updated_user_log_id
            )
            if user_updated:
                logger.debug(
                    f"[Leveling _update_member_profile_data()] updated the member profile data"
                    f" in the database for member {member} with id [{updated_user_id}] "
                    f"{index + 1}/{total_number_of_updates_needed}"
                )
            elif user_processed:
                logger.debug(
                    f"[Leveling _update_member_profile_data()] processed the member profile data"
                    f" in the database for member {member} with id [{updated_user_id}] that had no updates "
                    f"{index + 1}/{total_number_of_updates_needed}"
                )
        except Exception as e:
            log_exception(
                logger,
                f"[Leveling _update_member_profile_data()] unable to update the member profile data in"
                f" the database for member {member} with id [{updated_user_id}] and updated_user_log_id = "
                f"{updated_user_log_id} {index + 1}/{total_number_of_updates_needed}",
                error=e
            )
        return user_updated, user_processed

    @app_commands.command(name="reset_attempts")
    @app_commands.checks.has_any_role("Bot_manager")
    async def reset_attempts(self, interaction: discord.Interaction, member_id: str):
        self.update_outdated_profile_pics_logger.debug(
            f"[Leveling reset_user_profiles()] resetting attempts for [{member_id}] to 0"
        )
        e_obj = None
        if member_id.isdigit():
            member_id = int(member_id)
        else:
            e_obj = await embed(
                self.logger, interaction=interaction,
                description=f'Invalid ID of {member_id} detected',
                colour=COLOUR_MAPPING[WallEColour.ERROR]
            )
        if e_obj is None:
            if member_id not in self.user_points:
                e_obj = await embed(
                    self.logger, interaction=interaction,
                    description=f'No user with ID {member_id}',
                    colour=COLOUR_MAPPING[WallEColour.ERROR]
                )
            else:
                self.user_points[member_id].leveling_update_attempt = 0
                await self.user_points[member_id].async_save()
                e_obj = await embed(
                    self.logger, interaction=interaction,
                    description=f'<@{member_id}> attempts set to 0'
                )
        if e_obj:
            await interaction.response.send_message(embed=e_obj)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

    @app_commands.command(name="reset_user_profiles")
    @app_commands.checks.has_any_role("Bot_manager")
    async def reset_user_profiles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.bucket_update_in_progress:
            e_obj = await embed(
                self.logger, interaction=interaction,
                description='Another process is already updating the bucket numbers'
            )
            if e_obj:
                await interaction.followup.send(embed=e_obj)
                await asyncio.sleep(5)
                await interaction.delete_original_response()
            return
        self.bucket_update_in_progress = True
        users_to_update = []
        number_of_user_points = len(self.user_points)
        for indx, user_id in enumerate(self.user_points.keys()):
            self.user_points[user_id].bucket_number = None
            self.user_points[user_id].leveling_update_attempt = 0
            self.user_points[user_id].avatar_url = None
            self.user_points[user_id].avatar_url_message_id = None
            self.user_points[user_id].leveling_message_avatar_url = None
            self.user_points[user_id].discord_avatar_link_expiry_date = None
            users_to_update.append(self.user_points[user_id])
            self.logger.debug(f"[Leveling reset_user_profiles()] {indx}/ {number_of_user_points} UserPoints reset")

        user_lower_bound = 0
        number_of_users_per_update = 50
        user_upper_bound = number_of_users_per_update
        number_of_users_to_update = len(users_to_update)
        while user_lower_bound < number_of_users_to_update:
            await UserPoint.async_bulk_update(
                users_to_update[user_lower_bound:user_upper_bound],
                ["bucket_number", "leveling_update_attempt", "avatar_url", "avatar_url_message_id",
                 "leveling_message_avatar_url", "discord_avatar_link_expiry_date"
                 ]
            )
            self.logger.debug(
                f"[Leveling reset_user_profiles()] users between [{user_lower_bound},{user_upper_bound}) "
                f"updated out of {number_of_users_to_update}"
            )
            user_lower_bound = user_upper_bound
            user_upper_bound += number_of_users_per_update
        e_obj = await embed(
            self.logger, interaction=interaction,
            description=f'{len(users_to_update)} bucket_numbers reset to None'
        )
        if e_obj:
            await interaction.followup.send(embed=e_obj)
            await asyncio.sleep(5)
            await interaction.delete_original_response()
        if self.levelling_website_avatar_channel is not None:
            await self.levelling_website_avatar_channel.delete()
        leveling_website_avatar_images_channel_id = await bot.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, wall_e_config.get_config_value('basic_config', 'ENVIRONMENT'),
            'leveling_website_avatar_images'
        )
        self.levelling_website_avatar_channel: discord.TextChannel = discord.utils.get(
            self.guild.channels, id=leveling_website_avatar_images_channel_id
        )
        self.logger.debug(
            f"[Leveling reset_user_profiles()] bot channel {self.levelling_website_avatar_channel} acquired."
        )
        self.bucket_update_in_progress = False

    @commands.command(
        brief="associates an XP level with the role with the specified name",
        help=(
            'associates an existing role with the specified name for the specified level or it renames a '
            'role that is already assigned to the specified level\n\n'
            'Arguments:\n'
            '---level number: the number for the XP level to set\n'
            '---new role name: the name to set for the role associated with the XP level for "level number"\n\n'
            'Example:\n'
            '---.set_level_name 2 "Vim User"\n\n'
        ),
        usage='<level number> "new role name"'
    )
    @commands.has_any_role("Minions", "Moderator")
    async def set_level_name(self, ctx, level_number: int, new_role_name: str):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        self.logger.info(
            f"[Leveling set_level_name()] received request to set name for level {level_number} to {new_role_name} "
            f"from {ctx.author}"
        )
        existing_xp_level_with_specified_role_name = [
            level for level in self.levels.values() if level.role_name == new_role_name
        ]
        self.logger.debug(
            f"[Leveling set_level_name()] len(existing_xp_level_with_specified_role_name)="
            f"{len(existing_xp_level_with_specified_role_name)}"
        )
        if len(existing_xp_level_with_specified_role_name) > 0:
            await ctx.send(
                f"role {new_role_name} is already in use by level "
                f"{existing_xp_level_with_specified_role_name[0].number}",
                reference=ctx.message
            )
            return
        if level_number not in list(self.levels.keys()):
            self.logger.debug(f"[Leveling set_level_name()] {level_number} is not valid")
            current_levels = sorted([level.number for level in self.levels.values() if level.role_id is None])
            current_levels = [f"{level}" for level in current_levels]

            current_levels = ", ".join(current_levels)
            await ctx.send(
                f"you specified an incorrect level, the only levels available for setting their names "
                f"are :{current_levels}",
                reference=ctx.message
            )
            return
        if self.levels[level_number].role_id is None:
            self.logger.debug(f"[Leveling set_level_name()] no role_id detected for level {level_number}")
            # level does not yet have a role associated with it
            role = discord.utils.get(self.guild.roles, name=new_role_name)
            if role is None:
                self.logger.debug(
                    f"[Leveling set_level_name()] could not find the role {new_role_name}"
                    f" to associate with {level_number}"
                )
                await ctx.send(f"could not find role {new_role_name}. ", reference=ctx.message)
            else:
                self.logger.debug(
                    f"[Leveling set_level_name()] associating level {level_number} with role {new_role_name}"
                )
                await self.levels[level_number].set_level_name(new_role_name, role.id)
                self.levels_have_been_changed = True
                await ctx.send(
                    f"assigned role {new_role_name} for level {level_number}. "
                    f"Will take about 24 hours to apply role to the right people.\n\n"
                    f"Don't forget to correct the role position",
                    reference=ctx.message
                )

        else:
            self.logger.debug(f"[Leveling set_level_name()] role_id detected for level {level_number}")
            role = ctx.guild.get_role(self.levels[level_number].role_id)
            if role is None:
                self.logger.debug(
                    f"[Leveling set_level_name()] detected role_id detected for level {level_number} is invalid"
                )
                # the XP level is getting a new role since the role it was associated with was an error
                role = discord.utils.get(self.guild.roles, name=new_role_name)
                if role is None:
                    await ctx.send(f"could not find role {new_role_name}. ", reference=ctx.message)
                else:
                    await self.levels[level_number].set_level_name(new_role_name, role.id)
                    self.logger.debug(
                        f"[Leveling set_level_name()] set flag to associate level {level_number} with role"
                        f" {role.name}"
                    )
                    self.levels_have_been_changed = True
                    await ctx.send(
                        f"Associated role {new_role_name} for level {level_number}. "
                        f"Will take about 24 hours to apply role to the right people.\n\n"
                        f"Don't forget to correct the role position",
                        reference=ctx.message
                    )
            else:
                old_name = role.name
                self.logger.debug(
                    f"[Leveling set_level_name()] renaming role {old_name} to {new_role_name} for level"
                    f" {level_number}"
                )
                await role.edit(name=new_role_name)
                await self.levels[level_number].rename_level_name(new_role_name)
                await ctx.send(
                    f"renamed role {old_name} to {new_role_name} for level {level_number}",
                    reference=ctx.message
                )

    @commands.command(
        brief="unmaps the any role that is currently mapped to the specified level",
        help=(
            'de-associates an existing role with the specified name from the specified level\n\n'
            'Arguments:\n'
            '---level number: the number for the XP level to remove the role association from\n\n'
            'Example:\n'
            '---.remove_level_name 2\n\n'
        ),
        usage='<level number>'
    )
    @commands.has_any_role("Minions", "Moderator")
    async def remove_level_name(self, ctx, level_number: int):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        self.logger.info(
            f"[Leveling remove_level_name()] received request to set remove name for level {level_number} "
            f"from {ctx.author}"
        )
        if self.levels[level_number].role_id is None:
            self.logger.debug(
                f"[Leveling remove_level_name()] resetting role info to Null for level {level_number}"
            )
            await self.levels[level_number].remove_role()
            await ctx.send(
                f"level {level_number} does not have an existing role associated with it", reference=ctx.message
            )
            return
        self.logger.debug(
            f"[Leveling remove_level_name()] remove_level_name command detected from {ctx.author} with level_number"
            f" {level_number}"
        )
        role_name = self.levels[level_number].role_name
        await self.levels[level_number].remove_role()
        self.logger.debug(
            f"[Leveling remove_level_name()] resetting role info to Null for level {level_number}"
        )
        self.levels_have_been_changed = True
        await ctx.send(
            f"role {role_name} was disassociated from level {level_number}\n\n"
            f"Don't forget to delete the role",
            reference=ctx.message
        )

    @commands.command(
        brief="Get the XP rank for first tagged user or calling user",
        help=(
            'Arguments:\n'
            '---[@user] : the tagged user\'s whose rank to return\n\n'
            'Example:\n'
            '---.rank\n'
            '---.rank @user\n\n'
        ),
        usage='[@user]'
    )
    async def rank(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        message_author = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        message_author_id = message_author.id
        if message_author_id not in self.user_points:
            await ctx.send("specified user is not being tracked", reference=ctx.message)
            return
        if self.user_points[message_author_id].hidden and message_author_id != ctx.author.id:
            await ctx.send("This user has hidden their score", reference=ctx.message)
            return
        self.logger.info(f"[Leveling rank()] rank command detected from {ctx.author} for user {message_author}")
        xp_required_to_level_up = await self.user_points[message_author_id].get_xp_needed_to_level_up_to_next_level()

        description = f"""
        {self.user_points[message_author_id].level_up_specific_points} / {xp_required_to_level_up} XP

        Total Messages: {self.user_points[message_author_id].message_count}

        """
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            author=message_author,
            title=f"{message_author.display_name}'s Stat Card",
            content=[
                (
                    f"Rank # {await self.user_points[message_author_id].get_rank()}",
                    f"Level # {self.user_points[message_author_id].level_number}")
            ],
            description=description
        )
        if e_obj is not None:
            await ctx.send(embed=e_obj, reference=ctx.message)

    @commands.command(
        brief="Shows a list of all the XP levels and their associated roles and whether or not the roles exist"
    )
    @commands.has_any_role("Minions", "Moderator")
    async def levels(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        self.logger.info(f"[Leveling levels()] levels command detected from {ctx.author}")
        levels_with_a_role = [level for level in self.levels.values() if level.role_name is not None]
        levels_with_a_role.sort(key=lambda level: level.number)

        levels_with_a_valid_role = []
        levels_with_an_invalid_role = []
        for level_with_role in levels_with_a_role:
            role = discord.utils.get(self.guild.roles, name=level_with_role.role_name)
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

        await paginate_embed(self.logger, bot, descriptions_to_embed, title="Levels", ctx=ctx)

    @commands.command(brief="shows the current leaderboards")
    async def ranks(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        self.logger.info(f"[Leveling ranks()] ranks command detected from {ctx.author}")
        user_points = self.user_points.copy()
        user_points = [
            user_point for user_point in list(user_points.values())
            if (
                (user_point.user_id == ctx.author.id and user_point.hidden) or
                (user_point.user_id != ctx.author.id and not user_point.hidden)
            )
        ]
        user_points.sort(key=lambda x: x.points, reverse=True)
        descriptions_to_embed = []
        description_to_embed = "\nUser - Messages - Experience - Level\n"
        rank = 1
        for (index, user_point) in enumerate(user_points):
            if index % 10 == 0 and index > 0:
                descriptions_to_embed.append(description_to_embed)
                description_to_embed = "\nRank - User - Messages - Experience - Level\n"
            description_to_embed += (
                f"{rank} - <@{user_point.user_id}> - {user_point.message_count} - {user_point.points}"
                f" - {user_point.level_number}\n"
            )
            rank += 1
        if description_to_embed != "\nUser - Messages - Experience - Level\n":
            descriptions_to_embed.append(description_to_embed)
        if len(descriptions_to_embed) == 0:
            await ctx.send("No users currently being tracked", reference=ctx.message)
        else:
            await paginate_embed(self.logger, bot, descriptions_to_embed, ctx=ctx)

    @commands.command(
        brief="Hide a user's ranking from .rank @user and .ranks",
        help=(
            'Arguments:\n'
            '---[@user] : the tagged user\'s whose rank to hide\n\n'
            'Example:\n'
            '---.hide_xp\n'
            '---.hide_xp @user\n\n'
        ),
        usage='[@user]'
    )
    async def hide_xp(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        user_to_hide = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        self.logger.info(
            f"[Leveling hide_xp()] hide_xp command detected from {ctx.author} with user {user_to_hide} specified"
        )
        if user_to_hide.id != ctx.author.id:
            user_roles = [
                role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
            ]
            if 'Minions' not in user_roles:
                await ctx.send(
                    "You do not have adequate permission to hide another user's rank, incident will be reported",
                    reference=ctx.message
                )
                return
        if self.user_points[user_to_hide.id].hidden:
            await ctx.send(
                "You are already hidden" if user_to_hide.id == ctx.author.id else
                f"User {user_to_hide} is already hidden",
                reference=ctx.message
            )
        else:
            await self.user_points[user_to_hide.id].hide_xp()
            await ctx.send(
                "You are now hidden" if user_to_hide.id == ctx.author.id else
                f"User {user_to_hide} is now hidden",
                reference=ctx.message
            )

    @commands.command(
        brief="Makes a user's ranking visible again in .rank @user and .ranks",
        help=(
            'Arguments:\n'
            '---[@user] : the tagged user\'s whose rank to show\n\n'
            'Example:\n'
            '---.show_xp\n'
            '---.show_xp @user\n\n'
        ),
        usage='[@user]'
    )
    async def show_xp(self, ctx):
        if not self.xp_system_ready:
            await ctx.send("level command is not yet ready...", reference=ctx.message)
            return
        user_to_show = ctx.author if len(ctx.message.mentions) == 0 else ctx.message.mentions[0]
        self.logger.info(
            f"[Leveling show_xp()] show_xp command detected from {ctx.author} with user {user_to_show} specified"
        )
        if user_to_show.id != ctx.author.id:
            user_roles = [
                role.name for role in sorted(ctx.author.roles, key=lambda x: int(x.position), reverse=True)
            ]
            if 'Minions' not in user_roles:
                await ctx.send(
                    "You do not have adequate permission to show another user's rank, incident will be reported",
                    reference=ctx.message
                )
                return

        if not self.user_points[user_to_show.id].hidden:
            await ctx.send(
                "You are already visible" if user_to_show.id == ctx.author.id else
                f"User {user_to_show} is already visible",
                reference=ctx.message
            )
        else:
            await self.user_points[user_to_show.id].show_xp()
            await ctx.send(
                "You are now visible" if user_to_show.id == ctx.author.id else
                f"User {user_to_show} is now visible",
                reference=ctx.message
            )


async def setup(bot):
    await bot.add_cog(Leveling())
