import discord
from discord.ext import commands
import logging
logger = logging.getLogger('wall_e')


def getClassName():
    return "ManageCog"


class ManageCog(commands.Cog):

    def __init__(self, bot, config):
        logger.info("[testenv.py __init__()] initializing the TestCog")
        bot.add_check(self.check_test_environment)
        self.bot = bot
        self.config = config

    @commands.command(hidden=True)
    async def debuginfo(self, ctx):
        logger.info("[testenv.py debuginfo()] debuginfo command detected from " + str(ctx.message.author))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            fmt = '```You are testing the latest commit of branch or pull request: {0}```'
            await ctx.send(fmt.format(self.config.get_config_value('database', 'BRANCH_NAME')))
        return

    # this command is used by the TEST guild to ensur that each TEST container will only process incoming commands
    # that originate from channels that match the name of their branch
    def check_test_environment(self, ctx):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') == 'TEST':
            if ctx.message.guild is not None and\
               ctx.channel.name != self.config.get_config_value('basic_config', 'BRANCH_NAME').lower():
                return False
        return True


    ####################################################
    # Function that gets called when the script cant ##
    # understand the command that the user invoked   ##
    ####################################################
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if self.check_test_environment(self.config, ctx):
            if isinstance(error, commands.MissingRequiredArgument):
                fmt = 'Missing argument: {0}'
                logger.error('[main.py on_command_error()] ' + fmt.format(error.param))
                eObj = await imported_embed(
                    ctx,
                    author=config.get_config_value('bot_profile', 'BOT_NAME'),
                    avatar=config.get_config_value('bot_profile', 'BOT_AVATAR'),
                    description=fmt.format(error.param)
                )
                if eObj is not False:
                    await ctx.send(embed=eObj)
            else:
                # only prints out an error to the log if the string that was entered doesnt contain just "."
                pattern = r'[^\.]'
                if re.search(pattern, str(error)[9:-14]):
                    # author = ctx.author.nick or ctx.author.name
                    # await ctx.send('Error:\n```Sorry '+author+', seems like the command
                    # \"'+str(error)[9:-14]+'\"" doesn\'t exist :(```')
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    return

    # this command is used by the TEST guild to create the channel from which this TEST container will process
    # commands
    async def on_ready(self):
        logger.info("[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels))
        if self.config.get_config_value("wall_e", "ENVIRONMENT") == 'TEST':
            logger.info(
                "[testenv.py on_ready()] aquired list of channels = " + str(self.bot.guilds[0].channels)
            )
            channels = self.bot.guilds[0].channels
            branch_name = self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
            if discord.utils.get(channels, name=branch_name) is None:
                logger.info(
                    "[testenv.py on_ready()] creating the text channel"
                    " " + self.config.get_config_value('basic_config', 'BRANCH_NAME').lower()
                    )
                await self.bot.guilds[0].create_text_channel(branch_name)
