import asyncio
import discord
import logging
import aiohttp
logger = logging.getLogger('wall_e')


##################################################################################################
# HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def determine_disconnect_issues(bot, config):
    await bot.wait_until_ready()
    # only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
    # Production is a permanant channel so that it can be persistent. As for localhost,
    # the idea was that this removes a dependence on the user to make the channel and shifts that
    # responsibility to the script itself. thereby requiring less effort from the user
    bot_log_channel = None
    env = config.get_config_value("basic_config", "ENVIRONMENT")
    branch_name = config.get_config_value("basic_config", "BRANCH_NAME")
    log_channel_name = "network_error_logs"
    if (env == "LOCALHOST" or env == "PRODUCTION") and log_channel_name == 'NONE':
        logger.info(
            "[debugger.py determine_disconnect_issues()] "
            "no name detected for bot log channel in settings....exit"
        )

    if env == "LOCALHOST":
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
        bot_log_channel = log_channel.id
    elif env == "TEST":
        log_channel_name = '{}_network_logs'.format(branch_name.lower())
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
        bot_log_channel = log_channel.id
    elif env == "PRODUCTION":
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        bot_log_channel = log_channel.id

    channel = bot.get_channel(bot_log_channel)  # channel ID goes here
    if channel is None:
        logger.error(
            "[debugger.py determine_disconnect_issues] could not retrieve the bot_log channel "
            "with id {} . Please investigate further".format(bot_log_channel)
        )
    else:
        logger.info(
            "[debugger.py determine_disconnect_issues] bot_log channel "
            "with id {} successfully retrieved.".format(bot_log_channel)
        )
        while not bot.is_closed():
            incrementor = 1
            while True:
                # done because discord has a character limit of 2000 for each message
                # so what basically happens is it first tries to send the full message, then if it cant, it
                # breaks it down into 2000 sizes messages and send them individually
                try:
                    await.channel.send(incrementor)
                    incrementor += 1
                except (aiohttp.ClientError):
                    exc_str = '{}: {}'.format(type(exc).__name__, exc)
                    logger.error(
                        '[debugger.py determine_disconnect_issues] encountered ClientError\n{}'.format(exc_str)
                    )
                except (discord.errors.HTTPException):
                    exc_str = '{}: {}'.format(type(exc).__name__, exc)
                    logger.error(
                        '[debugger.py determine_disconnect_issues] encountered HTTPException\n{}'.format(exc_str)
                    )
                except RuntimeError:
                    exc_str = '{}: {}'.format(type(exc).__name__, exc)
                    logger.error(
                        '[debugger.py determine_disconnect_issues] encountered RuntimeError\n{}'.format(exc_str)
                    )
                except Exception as exc:
                    exc_str = '{}: {}'.format(type(exc).__name__, exc)
                    logger.error(
                        '[debugger.py determine_disconnect_issues] encountered Exception\n{}'.format(exc_str)
                    )
                await asyncio.sleep(1)
