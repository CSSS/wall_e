import asyncio
import logging
from aiohttp import web
from discord.ext import commands


logger = logging.getLogger('wall_e')


class Web(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.site = None
        self.bot.loop.create_task(self.server())

    def cog_unload(self):
        asyncio.ensure_future(self.site.stop())

    async def server(self):
        async def handler(request):
            return web.Response(text='Hello, world')
        app = web.Application()
        app.router.add_get('/', handler)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, '0.0.0.0', 31337)
        await self.bot.wait_until_ready()
        logger.info('[Web server()] web to start')
        await self.site.start()
