from discord.ext import commands
from main import commandFolder
import json
import subprocess

import logging
logger = logging.getLogger('wall_e')

class Administration():

	async def botManager(self, ctx):
		for managers in self.admin['BOT_MANAGERS']:
			if str(ctx.message.author.id) in managers.values():
				return True
		return False

	def __init__(self, bot):
		logger.info("[Administration __init__()] attempting to load bot managers from bot_mangers.json")
		with open('commands_to_load/bot_managers.json') as f:
			TheAdmins = json.load(f)
		logger.info("[Administration __init__()] loaded bot_managers from bot_managers.json= "+str(TheAdmins))
		self.admin_list = TheAdmins
		self.bot = bot

	@commands.command()
	async def load(self, ctx, name):
		if await self.botManager(ctx):
			try:
				logger.info("[Administration load()] "+ctx.message.author+" successfully authenticated")
				self.bot.load_extension(commandFolder+name)
				await ctx.send("{} command loaded.".format(name))
				logger.info("[Administration load()] "+name+" has been successfully loaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("command load failed: {}, {}".format(type(e), str(e)))
				logger.error("[Administration load()] loading "+name+" failed :"+str(type(e)) +", "+ str(e))
		else:
			logger.error("[Administration load()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def unload(self, ctx, name):
		if await self.botManager(ctx):
			logger.info("[Administration unload()] "+ctx.message.author+" successfully authenticated")
			self.bot.unload_extension(commandFolder+name)
			await ctx.send("{} command unloaded".format(name))
			logger.info("[Administration unload()] "+name+" has been successfully loaded")
		else:
			logger.error("[Administration unload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def reload(self, ctx, name):
		if await self.botManager(ctx):
			logger.info("[Administration reload()] "+ctx.message.author+" successfully authenticated")
			self.bot.unload_extension(commandFolder+name)
			try:
				bot.load_extension(commandFolder+name)
				await ctx.send("`{} command reloaded`".format(commandFolder+name))
				logger.info("[Administration reload()] "+name+" has been successfully reloaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("Command load failed: {}, {}".format(type(e), str(e)))
				logger.error("[Administration load()] loading "+name+" failed :"+str(type(e)) +", "+ str(e))

		else:
			logger.error("[Administration reload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def exc(self, ctx, *args):
		if await self.botManager(ctx):
			logger.info("[Administration exc()] "+ctx.message.author+" successfully authenticated")
			query = " ".join(args)
			await ctx.send("```"+subprocess.getoutput(query)+"```")
		else:
			logger.error("[Administration exc()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")



def setup(bot):
	bot.add_cog(Administration(bot))