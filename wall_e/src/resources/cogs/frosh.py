from discord.ext import commands
import logging
from resources.utilities.embed import embed as em
logger = logging.getLogger('wall_e')


class Frosh(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    @commands.command()
    async def froshteam(self, ctx, *info):
        logger.info(f'[Frosh team()] team command detected from user {ctx.author}')
        logger.info(f'[Frosh team()] arguments given: {info}')

        if len(info) < 3:
            e_obj = await em(
                ctx,
                title='Missing Arguments',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR'),
                colour=0xA6192E,
                content=[('Error', 'You are missing arguments. Call `.help team` for how to use the command')],
                footer='Team Error'
            )
            await ctx.send(embed=e_obj)
            logger.info('[Frosh team()] Missing arguments, command ended')
            return

        # just gonna assume the provided stuff is all good
        e_obj = await em(
            ctx,
            title='CSSS Frosh 2020 Gaming Arena',
            author=ctx.author.display_name,
            avatar=ctx.author.avatar_url,
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
                e_obj.colour = int('0x'+color, base=16)
        except Exception:
            pass

        logger.info(f'[Frosh team()] team embed created with the following fields: {e_obj.fields}')

        await ctx.send(embed=e_obj)
