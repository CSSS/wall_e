from discord.ext import commands
import discord
from main import cogs
import subprocess

import logging
logger = logging.getLogger('wall_e')

class Administration():

	def __init__(self, bot):
		self.bot = bot

	def validCog(self, cog):
		for cog in cogs:
			if cog["name"] == cog:
				return True, cog["folder"]
		return False, ''

	@commands.command()
	async def load(self, ctx, name):
		logger.info("[Administration load()] load command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration load()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return
			try:
				self.bot.load_extension(folder + '.' + name)
				await ctx.send("{} command loaded.".format(name))
				logger.info("[Administration load()] " + name + " has been successfully loaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("command load failed: {}, {}".format(type(e), str(e)))
				logger.info("[Administration load()] loading " + name + " failed :"+str(type(e)) +", "+ str(e))
		else:
			logger.info("[Administration load()] unauthorized command attempt detected from "+ str(ctx.message.author))
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def unload(self, ctx, name):
		logger.info("[Administration unload()] unload command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration unload()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return

			self.bot.unload_extension(folder + '.' + name)
			await ctx.send("{} command unloaded".format(name))
			logger.info("[Administration unload()] " + name + " has been successfully loaded")
		else:
			logger.info("[Administration unload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def reload(self, ctx, name):
		logger.info("[Administration reload()] reload command detected from "+str(ctx.message.author))
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration reload()] "+str(ctx.message.author)+" successfully authenticated")
			valid, folder = self.validCog(name)
			if not valid:
				await ctx.send("```" + name + " isn't a real cog```")
				logger.info("[Administration load()] " + str(ctx.message.author) + " tried loading " + name + " which doesn't exist.")
				return
			
			self.bot.unload_extension(folder + '.' + name)
			try:
				self.bot.load_extension(folder + '.' + name)
				await ctx.send("`{} command reloaded`".format(folder + '.' + name))
				logger.info("[Administration reload()] "+name+" has been successfully reloaded")
			except(AttributeError, ImportError) as e:
				await ctx.send("Command load failed: {}, {}".format(type(e), str(e)))
				logger.info("[Administration load()] loading "+name+" failed :"+str(type(e)) +", "+ str(e))

		else:
			logger.info("[Administration reload()] unauthorized command attempt detected from "+ ctx.message.author)
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")

	@commands.command()
	async def exc(self, ctx, *args):
		logger.info("[Administration exc()] exc command detected from "+str(ctx.message.author) + "with arguments \""+" ".join(args)+"\"")
		if ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
			logger.info("[Administration exc()] "+str(ctx.message.author)+" successfully authenticated")
			query = " ".join(args)

			#this got implemented for cases when the output of the command is too big to send to the channel
			exitCode, output = subprocess.getstatusoutput(query)
			prefix = "truncated output=\n"
			if len(output)>2000 :
				logger.info("getting reduced")
				length = len(output)- (len(output) - 2000) #taking length of just output into account
				length = length - len(prefix) #taking length of prefix into account
				length = length - 6 #taking length of prefix into account
				length = length - 12 - len(str(exitCode)) #taking exit code info into account
				output=output[:length]
				await ctx.send("Exit Code: "+str(exitCode)+"\n"+prefix+"```"+output+"```")
			elif len(output) == 0:
				await ctx.send("Exit Code: "+str(exitCode)+"\n")
			else:
				await ctx.send("Exit Code: "+str(exitCode)+"\n```"+output+"```")
		else:
			logger.info("[Administration exc()] unauthorized command attempt detected from "+ str(ctx.message.author))
			await ctx.send("You do not have adequate permission to execute this command, incident will be reported")



def setup(bot):
	bot.add_cog(Administration(bot))
