import datetime
import importlib
import inspect
import os
import re
import sys

import traceback

import discord
import django
import time

from discord import Intents
from discord.ext import commands
from django.core.wsgi import get_wsgi_application

from resources.utilities.setup_logger import Loggers

from resources.utilities.bot_channel_manager import BotChannelManager
from resources.utilities.config.config import WallEConfig
from resources.utilities.log_channel import write_to_bot_log_channel
from resources.utilities.embed import embed as imported_embed
from resources.utilities.slash_command_checks import command_in_correct_test_guild_channel

logger, debug_log_file_absolute_path, sys_stream_error_log_file_absolute_path \
    = Loggers.get_logger(logger_name="wall_e")

wall_e_config = WallEConfig(os.environ['ENVIRONMENT'])

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_db_orm_settings")
django.setup()

from resources.cogs.manage_cog import ManageCog  # noqa: E402

application = get_wsgi_application()

intents = Intents.all()


class WalleBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=intents)
        self.bot_loop_manager = BotChannelManager(wall_e_config, self)
        self.uploading = False

    async def setup_hook(self) -> None:

        # load the code dealing with test server interaction
        try:
            await self.add_cog(ManageCog(self, wall_e_config, self.bot_loop_manager))
        except Exception as err:
            exception = f'{type(err).__name_}: {err}'
            raise Exception(f'[main.py] Failed to load test server code testenv\n{exception}')

        # removing default help command to allow for custom help command
        print("[main.py] default help command being removed")
        self.remove_command("help")

        # tries to load any commands specified in the_commands into the bot
        await self.add_custom_cog()
        print("commands cleared and synced")
        await super().setup_hook()

    async def remove_custom_cog(self, folder: str, module_name: str):
        cog_module = importlib.import_module(folder + module_name)
        class_names = inspect.getmembers(sys.modules[cog_module.__name__], inspect.isclass)
        for class_name in class_names:
            if class_name[0].lower() == module_name.lower():
                cog_class_to_load = class_name[1]
                cog_class_has_no_slash_commands = (
                    (not hasattr(cog_class_to_load, "__cog_app_commands__")) or
                    len(cog_class_to_load.__cog_app_commands__) == 0
                )  # adding this in cause
                # discord is just way to buggy to reliably unload and reload a slash command at this time
                if type(cog_class_to_load) is commands.cog.CogMeta and cog_class_has_no_slash_commands:
                    await self.remove_cog(class_name[0])

    async def add_custom_cog(self, module_path_and_name: str = None):
        adding_all_cogs = module_path_and_name is None
        cog_unloaded = False
        for cog in wall_e_config.get_cogs():
            if cog_unloaded:
                break
            try:
                guild = discord.Object(id=wall_e_config.get_config_value('basic_config', 'DISCORD_ID'))
                if adding_all_cogs or module_path_and_name == f"{cog['path']}{cog['name']}":
                    cog_module = importlib.import_module(f"{cog['path']}{cog['name']}")
                    classes_that_match = inspect.getmembers(sys.modules[cog_module.__name__], inspect.isclass)
                    for class_that_match in classes_that_match:
                        cog_class_to_load = getattr(cog_module, class_that_match[0])
                        if type(cog_class_to_load) is commands.cog.CogMeta:
                            print(f"[main.py] attempting to load cog {cog['name']}")
                            await self.add_cog(
                                cog_class_to_load(self, wall_e_config, self.bot_loop_manager),
                                guild=guild
                            )
                            print(f"[main.py] {cog['name']} successfully loaded")
                            if not adding_all_cogs:
                                cog_unloaded = True
                                break
            except Exception as err:
                exception = f'{type(err).__name__}: {err}'
                raise Exception(f'[main.py] Failed to load command {cog}\n{exception}')
                if adding_all_cogs:
                    time.sleep(20)
                    exit(1)


bot = WalleBot()


##################################################
# signals to all functions that use            ##
# "wait_until_ready" that the bot is now ready ##
# to start performing background tasks         ##
##################################################
@bot.event
async def on_ready():
    # tries to open log file in prep for write_to_bot_log_channel function
    if bot.uploading is False:
        try:
            print(f"[main.py] trying to open {debug_log_file_absolute_path} to be able to send "
                  "its output to #bot_log channel")
            chan_id = await bot.bot_loop_manager.create_or_get_channel_id_for_service(
                wall_e_config,
                "wall_e_debug"
            )
            bot.loop.create_task(write_to_bot_log_channel(bot, debug_log_file_absolute_path, chan_id))
            print(
                "[main.py] log file successfully opened and connection to "
                "bot_log channel has been made"
            )
            print(f"[main.py] trying to open {sys_stream_error_log_file_absolute_path} to be able to send "
                  "its output to #bot_log channel")
            chan_id = await bot.bot_loop_manager.create_or_get_channel_id_for_service(
                wall_e_config,
                "wall_e_error"
            )
            bot.loop.create_task(write_to_bot_log_channel(bot, sys_stream_error_log_file_absolute_path, chan_id))
            print(
                "[main.py] log file successfully opened and connection to "
                "bot_log channel has been made"
            )
            bot.uploading = True
        except Exception as e:
            raise Exception(
                "[main.py] Could not open log file to read from and sent entries to bot_log channel due to "
                f"following error {e}")
    print('[main.py on_ready()] Logged in as')
    print(f'[main.py on_ready()] {bot.user.name}')
    print(f'[main.py on_ready()] {bot.user.id}')
    print('[main.py on_ready()] ------')
    wall_e_config.set_config_value("bot_profile", "BOT_NAME", bot.user.name)
    wall_e_config.set_config_value("bot_profile", "BOT_AVATAR", bot.user.avatar.url)
    print(
        "[main.py on_ready()] BOT_NAME initialized to"
        f" {wall_e_config.get_config_value('bot_profile', 'BOT_NAME')}"
    )
    print(
        "[main.py on_ready()] BOT_AVATAR initialized to "
        f"{wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR')}"

    )
    print(f"[main.py on_ready()] {bot.user.name} is now ready for commands")


########################################################
# Function that gets called any input or output from ##
# the script					     ##
########################################################
@bot.event
async def on_message(message):
    if message.guild is None and message.author != bot.user:
        em = await imported_embed(
            logger,
            ctx=message.author,
            description="[welcome to the machine](https://platform.openai.com/login?launch)"
        )
        if em is not None:
            await message.author.send(embed=em)
    else:
        await bot.process_commands(message)


########################################################
# Function that gets called whenever a commmand      ##
# gets called, being use for data gathering purposes ##
########################################################
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, cmd: discord.app_commands.commands.Command):

    database_enabled = wall_e_config.enabled("database_config", option="DB_ENABLED")
    correct_channel = await command_in_correct_test_guild_channel(wall_e_config, interaction)
    if correct_channel and database_enabled:
        from WalleModels.models import CommandStat
        await CommandStat.save_command_async(CommandStat(
            epoch_time=datetime.datetime.now().timestamp(), channel_name=interaction.channel.name,
            command=interaction.command.name, invoked_with=cmd.qualified_name,
            invoked_subcommand=None
        ))


####################################################
# Function that gets called when the script cant ##
# understand the command that the user invoked   ##
####################################################
@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error):
    if command_in_correct_test_guild_channel(wall_e_config, interaction):
        if isinstance(error, commands.MissingRequiredArgument):
            logger.error(f'[ManageCog on_command_error()] Missing argument: {error.param}')
            e_obj = await imported_embed(
                logger,
                interaction=interaction,
                author=wall_e_config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=wall_e_config.get_config_value('bot_profile', 'BOT_AVATAR'),
                description=f"Missing argument: {error.param}"
            )
            if e_obj is not False:
                await interaction.response.send_message(embed=e_obj)
        elif isinstance(error, commands.errors.CommandNotFound):
            return
        else:
            # only prints out an error to the log if the string that was entered doesnt contain just "."
            pattern = r'[^\.]'
            if re.search(pattern, f"{error}"[9:-14]):
                if type(error) is discord.ext.commands.errors.CheckFailure:
                    raise Exception(
                        f"[ManageCog on_command_error()] user {interaction.user} "
                        "probably tried to access a command they arent supposed to"
                    )
                else:
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    return

####################
# STARTING POINT ##
####################
if __name__ == "__main__":
    print("[main.py] Wall-E is starting up")

    # final step, running the bot with the passed in environment TOKEN variable
    bot.run(wall_e_config.get_config_value("basic_config", "TOKEN"), log_handler=logging.StreamHandler(sys.stdout))
