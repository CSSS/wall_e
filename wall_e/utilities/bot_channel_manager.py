import asyncio

import discord

from utilities.setup_logger import log_exception

wall_e_category_name = "WALL-E LOGS"
wall_e_category_name_contd = "WALL-E LOGS Contd"


class BotChannelManager:

    log_positioning = {}

    def __init__(self, config, bot):
        """
        Initialized the BotChannelManager service which is responsible for creating any discord text channels
        or category channels need by wall_e
        :param config: an instance of WALLEConfig that is used to determine what name to assign to the channels.
        :param bot: Used by the methods to make sure the service only tries to interact with discord API when
        bot.wait_until_ready() indicates the bot is ready
        """
        self.bot = bot
        self.channel_names = {
            "general_channel": {},
            "role_commands": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL')
            },
            "reminders": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL')
            },
            "ban": {
                "PRODUCTION": config.get_config_value('channel_names', 'MOD_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'MOD_CHANNEL')
            },
            "council": {
                "PRODUCTION": config.get_config_value('channel_names', 'MOD_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'MOD_CHANNEL')
            },
            "leveling": {
                "PRODUCTION": config.get_config_value('channel_names', 'LEVELLING_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'LEVELLING_CHANNEL')
            },
            "announcements": {
                "PRODUCTION": config.get_config_value('channel_names', 'ANNOUNCEMENTS_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'ANNOUNCEMENTS_CHANNEL')
            },
            "embed_avatars": {
                "PRODUCTION": config.get_config_value('channel_names', 'EMBED_AVATAR_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'EMBED_AVATAR_CHANNEL')
            },
            "incident_reports": {
                "PRODUCTION": config.get_config_value('channel_names', 'INCIDENT_REPORT_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'INCIDENT_REPORT_CHANNEL')
            },
            "leveling_website_avatar_images": {
                "PRODUCTION": config.get_config_value('channel_names', 'LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'LEVELLING_WEBSITE_AVATAR_IMAGE_CHANNEL')
            },
            "bot_management_channel": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_MANAGEMENT_CHANNEL'),
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_MANAGEMENT_CHANNEL')
            }
        }
        self.channel_obtained = {
        }
        log_names = [
            "sys_debug",
            "sys_warn",
            "sys_error",
            "wall_e_debug",
            "wall_e_warn",
            "wall_e_error",
            "discordpy_debug",
            "discordpy_warn",
            "discordpy_error",
            "administration_debug",
            "administration_warn",
            "administration_error",
            "ban_debug",
            "ban_warn",
            "ban_error",
            "health_checks_debug",
            "health_checks_warn",
            "health_checks_error",
            "here_debug",
            "here_warn",
            "here_error",
            "process_lurkers",
            "update_outdated_profile_pics",
            "update_outdated_profile_pics_warn",
            "update_outdated_profile_pics_error",
            "leveling_debug",
            "leveling_warn",
            "leveling_error",
            "misc_debug",
            "misc_warn",
            "misc_error",
            "mod_debug",
            "mod_warn",
            "mod_error",
            "reminders_debug",
            "reminders_warn",
            "reminders_error",
            "reaction_role_debug",
            "reaction_role_warn",
            "reaction_role_error",
            "role_commands_debug",
            "role_commands_warn",
            "role_commands_error",
            "sfu_debug",
            "sfu_warn",
            "sfu_error",
            "member_update_listener_debug",
            "member_update_listener_warn",
            "member_update_listener_error",
            "member_update_listener_discordpy_debug",
            "member_update_listener_discordpy_warn",
            "member_update_listener_discordpy_error",
        ]
        index = 0
        category = wall_e_category_name
        for channel_name in log_names:
            BotChannelManager.log_positioning[channel_name] = {
                "category": category,
                "index": index
            }
            index += 1
            if index == 50:
                index = 0
                category = wall_e_category_name_contd

    async def create_or_get_channel_id_for_service_logs(self, logger, guild, config, service):
        """
        used to create or get the text channels where log files entries will be uploaded to
        :param logger: the service's instant of logger
        :param guild: the guild on which to create or get the text channel
        :param config: used to determine the name of the text channels
        :param service: the service that is calling this method to get the necessary channel id
        :return: the ID of the channel
        """
        await self.bot.wait_until_ready()
        service = service.lower()
        environment = config.get_config_value("basic_config", "ENVIRONMENT")
        text_channel_position_info = BotChannelManager.log_positioning[service]
        text_channel_position = text_channel_position_info['index']
        logger.debug(
            f"[BotChannelManager create_or_get_channel_id_for_service_logs()] getting channel {service} for"
            f" {environment}"
        )
        logger.debug(
            f"[BotChannelManager create_or_get_channel_id_for_service_logs()] attempting to get  channel '{service}'"
            f" for {environment} "
        )
        bot_chan: discord.channel.CategoryChannel = discord.utils.get(guild.channels, name=service)
        if bot_chan is None:
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id_for_service_logs()] channel \"{service}\" for "
                f"{environment} does not exist will attempt to create it now."
            )
        number_of_retries_to_attempt = 10
        number_of_retries = 0
        while bot_chan is None and number_of_retries < number_of_retries_to_attempt:
            bot_chan = await guild.create_text_channel(
                service, position=text_channel_position
            )
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id_for_service_logs()] got channel \"{bot_chan}\" for "
                f"{environment}"
            )
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id_for_service_logs()] attempt ({number_of_retries}/"
                f"{number_of_retries_to_attempt}) for getting {service}"
            )
            await asyncio.sleep(10)
            number_of_retries += 1
        if bot_chan is None:
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id_for_service_logs()] the channel {service} "
                f"in {environment}  does not exist and I was unable to create it, exiting now...."
            )
            await asyncio.sleep(20)  # this is just here so that the above log line
            # gets a chance to get printed to discord
            exit(1)

        logger.debug(
            f"[BotChannelManager create_or_get_channel_id_for_service_logs()] the channel {service} for "
            f"in {environment} acquired."
        )
        logger.debug(
            f"[BotChannelManager create_or_get_channel_id_for_service_logs()] returning channel id for {service} for "
            f"{environment}"
        )
        return bot_chan.id

    async def create_or_get_channel_id(self, logger, guild, environment, channel_purpose):
        """
        used to create or get the text channels where things like reminders or mod-related messages
         need to be sent to
        :param logger: the service's instance of logger
        :param guild: the guild on which to create or get the text channel
        :param environment: the environment that wall_e is running in
        :param channel_purpose: the purpose the channel wil be used for, the options are keys in the
         self.channel_names dict instantiated in the constructor
        :return: the ID of the channel
        """
        await self.bot.wait_until_ready()
        channel_name = self.channel_names[channel_purpose][environment]
        logger.debug(
            f"[BotChannelManager create_or_get_channel_id()] getting channel {channel_name} for {environment} "
            f"{channel_purpose}"
        )
        if channel_name not in self.channel_obtained:
            self.channel_obtained[channel_name] = None
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id()] attempting to get  channel '{channel_name}' "
                f"for {environment} {channel_purpose} "
            )
            bot_chan: discord.channel.CategoryChannel = discord.utils.get(guild.channels, name=channel_name)
            if bot_chan is None:
                logger.debug(
                    f"[BotChannelManager create_or_get_channel_id()] channel \"{channel_name}\" for {environment} "
                    f"{channel_purpose} does not exist will attempt to create it now."
                )
            number_of_retries_to_attempt = 10
            number_of_retries = 0
            while bot_chan is None and number_of_retries < number_of_retries_to_attempt:
                bot_chan = await guild.create_text_channel(channel_name)
                logger.debug(
                    f"[BotChannelManager create_or_get_channel_id()] got channel \"{bot_chan}\" for {environment}"
                    f" {channel_purpose}"
                )
                logger.debug(
                    f"[BotChannelManager get_bot_general_channel()] attempt ({number_of_retries}/"
                    f"{number_of_retries_to_attempt}) for getting {channel_name} "
                )
                await asyncio.sleep(10)
                number_of_retries += 1
            if bot_chan is None:
                logger.debug(
                    f"[BotChannelManager create_or_get_channel_id()] the channel {channel_name} for "
                    f"{channel_purpose} "
                    f"in {environment}  does not exist and I was unable to create it, exiting now...."
                )
                await asyncio.sleep(20)  # this is just here so that the above log line
                # gets a chance to get printed to discord
                exit(1)
            logger.debug(
                f"[BotChannelManager create_or_get_channel_id()] the channel {channel_name} for {channel_purpose} "
                f"in {environment} acquired."
            )
            self.channel_obtained[channel_name] = bot_chan.id
        else:
            while self.channel_obtained[channel_name] is None:
                logger.debug(
                    f"[BotChannelManager create_or_get_channel_id()] waiting to get channel "
                    f"{channel_name} for {channel_purpose} "
                    f"in {environment}."
                )
                await asyncio.sleep(8)
        logger.debug(
            f"[BotChannelManager get_bot_general_channel()] returning channel id for {channel_name} for "
            f"{environment} {channel_purpose}"
        )
        return self.channel_obtained[channel_name]

    @classmethod
    async def delete_log_channels(cls, interaction: discord.Interaction):
        """
        Used to delete all the log text and category channels. Useful when doing local devving and want to clean up
        channels that are not needed after done devving
        :param interaction: the interaction object that can be traversed to contain the current list of
         channels in the guild
        :return:
        """

        def text_log_channel(channel): return (
            type(channel) == discord.channel.TextChannel and
            channel.name in list(BotChannelManager.log_positioning.keys())
        )

        def log_category(channel): return (
            type(channel) == discord.channel.CategoryChannel and
            channel.name in [wall_e_category_name, wall_e_category_name_contd]
        )

        log_channels = [
            channel for channel in list(interaction.guild.channels)
            if text_log_channel(channel) or log_category(channel)
        ]
        for log_channel in log_channels:
            await log_channel.delete()

    @classmethod
    async def fix_text_channel_positioning(cls, logger, guild):
        duplicate_channels = {}  # used to find and report text log channels that share the same name

        category_names = [wall_e_category_name_contd, wall_e_category_name]
        category_channels = {
        }
        for category_name in category_names:
            if category_name not in category_channels:
                category_channels[category_name] = None
                logs_category = discord.utils.get(guild.channels, name=category_name)
                if logs_category is None:
                    logs_category = await guild.create_category(name=category_name)
                category_channels[category_name] = logs_category.id
            else:
                logs_category = discord.utils.get(guild.channels, id=int(category_channels[category_name]))
            logger.debug(
                "[BotChannelManager fix_text_channel_positioning()] going through any logs under channel "
                f"{category_name}"
            )
            logger.debug(f"[BotChannelManager fix_text_channel_positioning()] got category {logs_category}")
            channels_under_category = [
                channel for channel in guild.channels
                if type(channel) == discord.channel.TextChannel and channel.category == logs_category
            ]
            for channel_under_category in channels_under_category:
                if channel_under_category.name not in duplicate_channels:
                    duplicate_channels[channel_under_category.name] = 1
                else:
                    duplicate_channels[channel_under_category.name] += 1

                # ensure that there are no channels that should not exist
                if channel_under_category.name not in BotChannelManager.log_positioning:
                    await channel_under_category.delete()
            number_of_clean_passes = 0
            while number_of_clean_passes < 3:
                # encapsulating the whole thing in a while loop cause sometimes a channel might erroneously get pushed
                # to the bottom while the repositioning is happening, which necessitates another sweep-through
                # as such, I am going to make the code keep going over the channels until all the positions are
                # verified as what they should be
                position_edited = False
                for text_channel_name, text_channel_position_info in BotChannelManager.log_positioning.items():
                    if text_channel_position_info['category'] != category_name:
                        continue
                    index = text_channel_position_info['index']
                    text_channel = discord.utils.get(guild.channels, name=text_channel_name)
                    while text_channel is None:
                        logger.warn(
                            f"[BotChannelManager fix_text_channel_positioning()] unable to get channel "
                            f"[{text_channel_name}], retrying in 5 seconds"
                        )
                        await asyncio.sleep(5)
                        text_channel = discord.utils.get(guild.channels, name=text_channel_name)
                    if text_channel.category != logs_category:
                        logger.debug(
                            f"[BotChannelManager fix_text_channel_positioning()] fixing the category for "
                            f"{text_channel_name} {logs_category}"
                        )
                        position_edited = True
                        await text_channel.edit(category=logs_category)
                    if text_channel.position != index:
                        logger.debug(
                            f"[BotChannelManager fix_text_channel_positioning()] changing the position for "
                            f"{text_channel_name} from {text_channel.position} to {index}"
                        )
                        position_edited = True
                        await text_channel.edit(position=index)
                if position_edited:
                    number_of_clean_passes = 0
                    logger.warn(
                        "[BotChannelManager fix_text_channel_positioning()] doing another sweep of the log text "
                        "channels positioning"
                    )
                else:
                    number_of_clean_passes += 1
        duplicate_channels = [
            channel_name
            for channel_name, number_of_occurrences in duplicate_channels.items()
            if number_of_occurrences > 1
        ]
        if len(duplicate_channels) > 0:
            duplicate_channels = ", ".join(duplicate_channels)
            log_exception(
                logger,
                f"[BotChannelManager fix_text_channel_positioning()] following duplicate"
                f" text log channels detected: {duplicate_channels}"
            )
        logger.debug(
            "[BotChannelManager fix_text_channel_positioning()] done with sweep of the log text channels "
            "positioning"
        )
