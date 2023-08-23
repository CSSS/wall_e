from discord.ext import commands
from resources.utilities.embed import embed as em
from resources.utilities.log_channel import write_to_bot_log_channel
from resources.utilities.setup_logger import Loggers


class Frosh(commands.Cog):

    def __init__(self, bot, config, bot_loop_manager):
        self.bot = bot
        self.config = config
        self.bot_loop_manager = bot_loop_manager
        self.logger, self.debug_log_file_absolute_path, self.sys_stream_error_log_file_absolute_path \
            = Loggers.get_logger(logger_name="Frosh")

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        chan_id = await self.bot_loop_manager.create_or_get_channel_id_for_service(
            self.config,
            "frosh_debug"
        )
        await write_to_bot_log_channel(
            self.bot, self.debug_log_file_absolute_path, chan_id
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        chan_id = await self.bot_loop_manager.create_or_get_channel_id_for_service(
            self.config,
            "frosh_error"
        )
        await write_to_bot_log_channel(
            self.bot, self.sys_stream_error_log_file_absolute_path, chan_id
        )

    @commands.command(aliases=["team"])
    async def froshteam(self, ctx, *info):
        self.logger.info(f'[Frosh team()] team command detected from user {ctx.author}')
        self.logger.info(f'[Frosh team()] arguments given: {info}')

        if len(info) < 3:
            e_obj = await em(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xA6192E,
                content=[('Error', 'You are missing arguments. Call `.help team` for how to use the command')],
                footer='Team Error'
            )
            await ctx.send(embed=e_obj)
            self.logger.info('[Frosh team()] Missing arguments, command ended')
            return

        # just gonna assume the provided stuff is all good
        e_obj = await em(
            self.logger,
            ctx=ctx,
            title='CSSS Frosh 2020 Gaming Arena',
            author=ctx.author.display_name,
            avatar=ctx.author.avatar.url,
            content=[
                ('Team Name', info[0]),
                ('Game', info[1]),
                ('Contact', ctx.author.mention),
                ('Team Members', '\n'.join(list(map(lambda str: str.strip(), info[2].split(',')))))
            ],
            footer='Frosh 2020'
        )

        try:
            if len(info) >= 4:
                color = info[3]
                if color[0] == '#':
                    color = color[1:]
                e_obj.colour = int('0x' + color, base=16)
        except Exception:
            pass

        self.logger.info(f'[Frosh team()] team embed created with the following fields: {e_obj.fields}')

        await ctx.send(embed=e_obj)

    @commands.command()
    async def reportwin(self, ctx, *info):
        self.logger.info(f'[Frosh reportwin()] team command detected from user {ctx.author}')
        self.logger.info(f'[Frosh reportwin()] arguments given: {info}')

        if len(info) < 2:
            e_obj = await em(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xA6192E,
                content=[('Error', 'You are missing arguments. Call `.help reportwin` for how to use the command')],
                footer='ReportWin Error'
            )
            await ctx.send(embed=e_obj)
            self.logger.info('[Frosh reportwin()] Missing arguments, command ended')
            return

        e_obj = await em(
            self.logger,
            ctx=ctx,
            title='CSSS Frosh 2020 Gaming Arena Winner',
            author=ctx.author.display_name,
            avatar=ctx.author.avatar.url,
            colour=0x00FF61,
            content=[
                ('Team Name', info[0]),
                ('Team Members', '\n'.join(list(map(lambda str: str.strip(), info[1].split(',')))))
            ],
            footer='Frosh 2020'
        )

        self.logger.info(f'[Frosh reportwin()] winner announcement embed made with following fields: {e_obj.fields}')
        await ctx.send(embed=e_obj)
