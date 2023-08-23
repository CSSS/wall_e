import asyncio
import logging

import discord

logger = logging.getLogger('wall_e')


class BotChannelManager:
    def __init__(self, config, bot):
        self.bot = bot
        self.channel_names = {
            "general_channel": {
                "TEST": config.get_config_value('basic_config', 'BRANCH_NAME').lower(),
            },
            "role_commands": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel",
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL')
            },
            "reminders": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel",
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_GENERAL_CHANNEL')
            },
            "log_channel": {
                "PRODUCTION": config.get_config_value('channel_names', 'BOT_LOG_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_logs",
                "LOCALHOST": config.get_config_value('channel_names', 'BOT_LOG_CHANNEL')
            },
            "ban": {
                "PRODUCTION": config.get_config_value('channel_names', 'MOD_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_mod_channel",
                "LOCALHOST": config.get_config_value('channel_names', 'MOD_CHANNEL')
            },
            "council": {
                "PRODUCTION": config.get_config_value('channel_names', 'MOD_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_mod_channel",
                "LOCALHOST": config.get_config_value('channel_names', 'MOD_CHANNEL')
            },
            "leveling": {
                "PRODUCTION": config.get_config_value('channel_names', 'LEVELLING_CHANNEL'),
                "TEST": f"{config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_council",
                "LOCALHOST": config.get_config_value('channel_names', 'LEVELLING_CHANNEL')
            }
        }
        self.channel_obtained = {
        }

    async def create_or_get_channel_id(self, environment, channel_purpose):
        await self.bot.wait_until_ready()
        channel_name = self.channel_names[channel_purpose][environment]
        logger.info("[BotChannelManager get_bot_general_channel()] "
                    f"getting channel {channel_name} for {environment} {channel_purpose}")
        if channel_name not in self.channel_obtained:
            self.channel_obtained[channel_name] = None
            logger.info("[BotChannelManager get_bot_general_channel()] attempting to get "
                        f" channel '{channel_name}' for {environment} {channel_purpose} ")
            bot_chan = discord.utils.get(self.bot.guilds[0].channels, name=channel_name)
            if bot_chan is None:
                logger.info("[BotChannelManager create_or_get_channel_id()] "
                            f"channel \"{channel_name}\" for {environment} {channel_purpose} does not exist "
                            f"will attempt to create it now.")
            number_of_retries_to_attempt = 10
            number_of_retries = 0
            while bot_chan is None and number_of_retries < number_of_retries_to_attempt:
                bot_chan = await self.bot.guilds[0].create_text_channel(channel_name)
                logger.info("[BotChannelManager create_or_get_channel_id()] "
                            f"got channel \"{bot_chan}\" for {environment} {channel_purpose}")
                logger.info("[BotChannelManager get_bot_general_channel()] attempt "
                            f"({number_of_retries}/{number_of_retries_to_attempt}) for getting {channel_name} ")
                await asyncio.sleep(10)
                number_of_retries += 1
            if bot_chan is None:
                logger.error(
                    f"[BotChannelManager create_or_get_channel_id()] the channel {channel_name} for "
                    f"{channel_purpose} "
                    f"in {environment}  does not exist and I was unable to create it, exiting now...."
                )
                await asyncio.sleep(20)  # this is just here so that the above log line
                # gets a chance to get printed to discord
                exit(1)
            logger.info(
                f"[BotChannelManager create_or_get_channel_id()] the channel {channel_name} for {channel_purpose} "
                f"in {environment} acquired."
            )
            self.channel_obtained[channel_name] = bot_chan.id
        else:
            while self.channel_obtained[channel_name] is None:
                logger.info(
                    f"[BotChannelManager create_or_get_channel_id()] waiting to get channel "
                    f"{channel_name} for {channel_purpose} "
                    f"in {environment}."
                )
                await asyncio.sleep(8)
        logger.info("[BotChannelManager get_bot_general_channel()] "
                    f"returning channel id for {channel_name} "
                    f"for {environment} {channel_purpose}")
        return self.channel_obtained[channel_name]
