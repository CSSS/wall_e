import asyncio
import discord
import logging
import aiohttp
logger = logging.getLogger('wall_e')


##################################################################################################
# HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel(bot, config, f):
    await bot.wait_until_ready()
    # only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
    # Production is a permanant channel so that it can be persistent. As for localhost,
    # the idea was that this removes a dependence on the user to make the channel and shifts that
    # responsibility to the script itself. thereby requiring less effort from the user
    bot_log_channel = None
    env = config.get_config_value("basic_config", "ENVIRONMENT")
    branch_name = config.get_config_value("basic_config", "BRANCH_NAME")
    log_channel_name = config.get_config_value("basic_config", "BOT_LOG_CHANNEL")
    if (env == "LOCALHOST" or env == "PRODUCTION") and log_channel_name == 'NONE':
        logger.info(
            "[log_channel.py write_to_bot_log_channel()] "
            "no name detected for bot log channel in settings....exit"
        )

    if env == "LOCALHOST":
        log_channel = discord.utils.get(bot.guilds[0].channels, name=log_channel_name)
        if log_channel is None:
            log_channel = await bot.guilds[0].create_text_channel(log_channel_name)
        bot_log_channel = log_channel.id
    elif env == "TEST":
        log_channel_name = '{}_logs'.format(branch_name.lower())
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
            "[log_channel.py write_to_bot_log_channel] could not retrieve the bot_log channel "
            "with id {} . Please investigate further".format(bot_log_channel)
        )
    else:
        logger.info(
            "[log_channel.py write_to_bot_log_channel] bot_log channel "
            "with id {} successfully retrieved.".format(bot_log_channel)
        )
        while not bot.is_closed():
            f.flush()
            line = f.readline()
            while line:
                if line.strip() != "":
                    # this was done so that no one gets accidentally pinged from the bot log channel
                    if '<@288148680479997963>' not in line:
                        line = line.replace("@", "[at]")
                    if line[0] == ' ':
                        line = ".{}".format(line)
                    output = line
                    # done because discord has a character limit of 2000 for each message
                    # so what basically happens is it first tries to send the full message, then if it cant, it
                    # breaks it down into 2000 sizes messages and send them individually
                    try:
                        await channel.send(output)
                    except (aiohttp.ClientError, discord.errors.HTTPException):
                        finished = False
                        first_index, last_index = 0, 2000
                        while not finished:
                            await channel.send(output[first_index:last_index])
                            first_index = last_index
                            last_index += 2000
                            if len(output[first_index:last_index]) == 0:
                                finished = True
                    except RuntimeError:
                        logger.info("[log_channel.py write_to_bot_log_channel] encountered RuntimeError, "
                                    " will assume that the user is attempting to exit")
                        break
                    except Exception as exc:
                        exc_str = '{}: {}'.format(type(exc).__name__, exc)
                        logger.error(
                            '[log_channel.py write_to_bot_log_channel] write to channel failed\n{}'.format(exc_str)
                        )
                line = f.readline()
            await asyncio.sleep(1)
