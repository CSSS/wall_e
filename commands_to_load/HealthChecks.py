from discord.ext import commands
from commands_to_load.Administration import Administration 
import discord.client
import json
from commands_to_load.Paginate import paginateEmbed, paginate

import logging
logger = logging.getLogger('wall_e')

class HealthChecks():

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		logger.info("[HealthChecks ping()] ping command detected from "+str(ctx.message.author))
		await ctx.send('```pong!```')


	@commands.command()
	async def echo(self, ctx, arg):
		user = ctx.author.nick or ctx.author.name
		logger.info("[HealthChecks echo()] echo command detected from "+str(ctx.message.author)+" with argument "+str(arg))
		await ctx.send(user + " says: " + arg)

	@commands.command()
	async def help(self, ctx):
		await ctx.send("     help me.....")
		logger.info("[HealthChecks help()] help command detected from "+str(ctx.message.author))
		logger.info("[HealthChecks help()] attempting to load command info from help.json")
		with open('commands_to_load/help.json') as f:
			helpDict = json.load(f)
		logger.info("[HealthChecks help()] loaded commands from help.json=\n"+str(json.dumps(helpDict, indent=3)))
		
		# determing the number of commands the user has access to.
		numberOfCommands=0
		for entry in helpDict['commands']:
			if entry['access'] == "bot_manager" and ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
				numberOfCommands += 1
			elif entry['access'] == "public":
				numberOfCommands += 1

		helpArr = [["" for x in range(2)] for y in range(numberOfCommands)] 
		index=0
		logger.info("[HealthChecks help()] tranferring dictionary to array")
		for entry in helpDict['commands']:
			if entry['access'] == "bot_manager" and ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
				helpArr[index][0]=entry['name']
				helpArr[index][1]=entry['description']
			elif entry['access'] == "public":
				helpArr[index][0]=entry['name']
				helpArr[index][1]=entry['description']
			index+=1
		logger.info("[HealthChecks help()] transfer successful")

		#rolesList = sorted(rolesList, key=str.lower)
		await paginateEmbed(bot=self.bot,title="Help Page" ,ctx=ctx,listToEmbed=helpArr, numOfPageEntries=5)


def setup(bot):
	bot.add_cog(HealthChecks(bot))
