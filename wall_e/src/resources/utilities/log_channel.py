import asyncio
import discord
import aiohttp


##################################################################################################
# HANDLES BACKGROUND TASK OF WRITING CONTENTS OF LOG FILE TO BOT_LOG CHANNEL ON DISCORD SERVER ##
##################################################################################################
async def write_to_bot_log_channel(bot, file_path, chan_id):
    # only environment that doesn't do automatic creation of the bot_log channel is the PRODUCTION guild.
    # Production is a permanent channel so that it can be persistent. As for localhost,
    # the idea was that this removes a dependence on the user to make the channel and shifts that
    # responsibility to the script itself. thereby requiring less effort from the user
    channel = discord.utils.get(
        bot.guilds[0].channels, id=chan_id
    )
    print(
        "[log_channel.py write_to_bot_log_channel] bot_log channel "
        f"with id {chan_id} successfully retrieved."
    )
    f = open(file_path, 'r')
    f.seek(0)
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
                    print("[log_channel.py write_to_bot_log_channel] encountered RuntimeError, "
                          " will assume that the user is attempting to exit")
                    break
                except Exception as exc:
                    exc_str = '{}: {}'.format(type(exc).__name__, exc)
                    raise Exception(
                        '[log_channel.py write_to_bot_log_channel] write to channel failed\n{}'.format(exc_str)
                    )
            line = f.readline()
        await asyncio.sleep(1)
