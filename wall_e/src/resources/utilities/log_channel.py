import asyncio
import discord
import logging
import aiohttp
logger = logging.getLogger('wall_e')


##################################################################################################
# HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel(bot, config, f, bot_loop_manager):
    # only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
    # Production is a permanent channel so that it can be persistent. As for localhost,
    # the idea was that this removes a dependence on the user to make the channel and shifts that
    # responsibility to the script itself. thereby requiring less effort from the user
    chan_id = await bot_loop_manager.create_or_get_channel_id(
        config.get_config_value("basic_config", "ENVIRONMENT"),
        "log_channel"
    )
    channel = discord.utils.get(
        bot.guilds[0].channels, id=chan_id
    )
    logger.info(
        "[log_channel.py write_to_bot_log_channel] bot_log channel "
        f"with id {chan_id} successfully retrieved."
    )
    while not bot.is_closed():
        f.flush()
        line = f.readline()
        while line:
            if line.strip() != "":
                # this was done so that no one gets accidentally pinged from the bot log channel
                line = line.replace("@", "[at]").replace('alertJace', '<@288148680479997963>')
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
