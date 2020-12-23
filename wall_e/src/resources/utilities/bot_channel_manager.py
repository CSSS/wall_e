import asyncio

import discord
import logging

logger = logging.getLogger('wall_e')


class BotChannelManager:
    def __init__(self, config, bot):
        self.bot = bot
        self.config = config
        self.channel_retrieved = False
        self.bot_channel_id = None
        self.bot_channel_name = None

        if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'PRODUCTION':
            self.bot_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')
        elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':\
            self.bot_channel_name = f"{self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()}_bot_channel"
        elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
            self.bot_channel_name = self.config.get_config_value('basic_config', 'BOT_GENERAL_CHANNEL')

    def get_bot_channel_name(self):
        return self.bot_channel_name

    async def retrieve_bot_channel(self):
        await self.bot.wait_until_ready()
        try:
            bot_channel_id = None
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'PRODUCTION':
                logger.info(
                    "[BotChannelManager __init__()] environment "
                    f"is =[{self.config.get_config_value('basic_config', 'ENVIRONMENT')}]"
                )
                bot_chan = discord.utils.get(self.bot.guilds[0].channels, name=self.bot_channel_name)
                if bot_chan is None:
                    logger.info("[BotChannelManager __init__()] bot channel does not exist in PRODUCTION.")
                    bot_chan = await self.bot.guilds[0].create_text_channel(self.bot_channel_name)
                    bot_channel_id = bot_chan.id
                    if bot_channel_id is None:
                        logger.info("[BotChannelManager __init__()] the channel designated for bot messages "
                                    f"[{self.bot_channel_name}] in PRODUCTION does not exist and I was unable to create "
                                    "it, exiting now....")
                        exit(1)
                    logger.info("[BotChannelManager __init__()] variable "
                                f"\"bot_channel_id\" is set to \"{bot_channel_id}\"")
                else:
                    logger.info("[BotChannelManager __init__()] bot channel exists in PRODUCTION and was detected.")
                    bot_channel_id = bot_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
                logger.info(
                    "[BotChannelManager __init__()] branch is "
                    f"=[{self.config.get_config_value('basic_config', 'BRANCH_NAME')}]"
                )

                bot_chan = discord.utils.get(
                    self.bot.guilds[0].channels,
                    name=self.bot_channel_name
                )
                if bot_chan is None:
                    bot_chan = await self.bot.guilds[0].create_text_channel(
                        self.bot_channel_name)
                    bot_channel_id = bot_chan.id
                    if bot_channel_id is None:
                        logger.info(
                            "[BotChannelManager __init__()] the channel designated for bot messages "
                            f"[{self.config.get_config_value('basic_config', 'BRANCH_NAME')}_bot_channel] in "
                            f"{self.config.get_config_value('basic_config', 'BRANCH_NAME')} "
                            "does not exist and I was unable to create it, exiting now...."
                        )
                        exit(1)
                    logger.info("[BotChannelManager __init__()] variable "
                                f"\"bot_channel_id\" is set to \"{bot_channel_id}\"")
                else:
                    logger.info(
                        "[BotChannelManager __init__()] bot channel exists in"
                        f" {self.config.get_config_value('basic_config', 'BRANCH_NAME')} and was "
                        "detected."
                    )
                    bot_channel_id = bot_chan.id
            elif self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'LOCALHOST':
                logger.info(
                    "[BotChannelManager __init__()] environment is"
                    f" =[{self.config.get_config_value('basic_config', 'ENVIRONMENT')}]"
                )
                bot_chan = discord.utils.get(self.bot.guilds[0].channels, name=self.bot_channel_name)
                if bot_chan is None:
                    logger.info("[BotChannelManager __init__()] bot channel does not exist in local dev.")
                    bot_chan = await self.bot.guilds[0].create_text_channel(self.bot_channel_name)
                    bot_channel_id = bot_chan.id
                    if bot_channel_id is None:
                        logger.info("[BotChannelManager __init__()] the channel designated for bot messages "
                                    f"[{self.bot_channel_name}] in local dev does not exist and I was unable to create it "
                                    "it, exiting now.....")
                        exit(1)
                    logger.info("[BotChannelManager __init__()] variables "
                                f"\"bot_channel_id is\" is set to \"{bot_channel_id}\"")
                else:
                    logger.info("[BotChannelManager __init__()] bot channel exists in local dev and was detected.")
                    bot_channel_id = bot_chan.id
            self.bot_channel_id = bot_channel_id
        except Exception as e:
            logger.error("[BotChannelManager __init__()] enountered following exception when connecting to bot "
                         f"channel\n{e}")
        self.channel_retrieved = True

    async def get_bot_channel(self, acquire_channel=False):
        if acquire_channel:
            await self.retrieve_bot_channel()
        else:
            while not self.channel_retrieved:
                await asyncio.sleep(3)
        return self.bot.get_channel(self.bot_channel_id) if self.bot_channel_id is not None else None
