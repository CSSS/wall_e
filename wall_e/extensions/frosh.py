import asyncio

from discord.ext import commands

from utilities.global_vars import bot, wall_e_config

from utilities.embed import embed as em, WallEColour
from utilities.file_uploading import start_file_uploading
from utilities.setup_logger import Loggers


class Frosh(commands.Cog):

    def __init__(self):
        log_info = Loggers.get_logger(logger_name="Frosh")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.logger.info("[Frosh __init__()] initializing Frosh")
        self.guild = None

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.debug_log_file_absolute_path, "frosh_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if wall_e_config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, bot, wall_e_config, self.error_log_file_absolute_path, "frosh_error"
            )

    @commands.command(
        brief="Creates an embed that holds details about your Frosh game team.",
        help=(
            'Need help picking a colour?\n[HTML Colour Codes](https://htmlcolorcodes.com/color-picker/)\n\n'
            'Arguments:\n'
            '---team name: the name for the team\n'
            '---game name: the name of the game\n'
            '---team member names: a comma separate list of the team names'
            '---[colour]: the hex code/value for embed colour\n\n'
            'Examples:\n'
            '---.team "JL" "Super Tag" "Jon, Bruce, Clark, Diana, Barry"\n'
            '---.team "team 1337" "PacMacro" "Jeffrey, Harry, Noble, Ali" "#E8C100"\n'
            '---.team "Z fighters" "Cell Games" "Goku, Vegeta, Uub, Beerus" "4CD100"\n\n'
        ),
        usage='"team name "game name" "team member names" [hex color]',
        aliases=["team"]
    )
    async def froshteam(self, ctx, *info):
        self.logger.info(
            f'[Frosh froshteam()] team command detected from user {ctx.author} with arguments: {info}'
        )

        if len(info) < 3:
            e_obj = await em(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=ctx.me,
                colour=WallEColour.ERROR,
                content=[('Error', 'You are missing arguments. Call `.help team` for how to use the command')],
                footer='Team Error'
            )
            await ctx.send(embed=e_obj)
            self.logger.debug('[Frosh froshteam()] Missing arguments, command ended')
            return

        # just gonna assume the provided stuff is all good
        e_obj = await em(
            self.logger,
            ctx=ctx,
            title='CSSS Frosh 2020 Gaming Arena',
            author=ctx.author,
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

        self.logger.debug(f'[Frosh froshteam()] team embed created with the following fields: {e_obj.fields}')

        await ctx.send(embed=e_obj)

    @commands.command(
        brief="Creates an embed that report a win for your team.",
        help=(
            'Arguments:\n'
            '---team name: the name for the team\n'
            '---team member names: a comma separate list of the team names\n\n'
            'Examples:\n'
            '---.reportwin "team 1337" "Jeffrey, Harry, Noble, Ali"'
        ),
        usage='"team name "team member names"',
    )
    async def reportwin(self, ctx, *info):
        self.logger.info(f'[Frosh reportwin()] team command detected from user {ctx.author} with arguments: {info}')
        if len(info) < 2:
            e_obj = await em(
                self.logger,
                ctx=ctx,
                title='Missing Arguments',
                author=ctx.me,
                colour=WallEColour.ERROR,
                content=[('Error', 'You are missing arguments. Call `.help reportwin` for how to use the command')],
                footer='ReportWin Error'
            )
            await ctx.send(embed=e_obj)
            self.logger.debug('[Frosh reportwin()] Missing arguments, command ended')
            return

        e_obj = await em(
            self.logger,
            ctx=ctx,
            title='CSSS Frosh 2020 Gaming Arena Winner',
            author=ctx.author,
            colour=WallEColour.FROSH_2020_THEME,
            content=[
                ('Team Name', info[0]),
                ('Team Members', '\n'.join(list(map(lambda str: str.strip(), info[1].split(',')))))
            ],
            footer='Frosh 2020'
        )

        self.logger.debug(f'[Frosh reportwin()] winner announcement embed made with following fields: {e_obj.fields}')
        await ctx.send(embed=e_obj)


async def setup(bot):
    await bot.add_cog(Frosh())
