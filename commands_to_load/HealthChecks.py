from discord.ext import commands
import discord.client
import json
from helper_files.Paginate import paginateEmbed, paginate
from helper_files.embed import embed 
import helper_files.settings as settings

import logging
logger = logging.getLogger('wall_e')

class HealthChecks():

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		logger.info("[HealthChecks ping()] ping command detected from "+str(ctx.message.author))
		eObj = embed(description='Pong!', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR)
		await ctx.send(embed=eObj)


	@commands.command()
	async def echo(self, ctx, *args):
		user = ctx.author.display_name
		arg=''
		for argument in args:
			arg+=argument+' '
		logger.info("[HealthChecks echo()] echo command detected from "+str(ctx.message.author)+" with argument "+str(arg))
		avatar = ctx.author.avatar_url
		eObj = embed(author=user, avatar=avatar, description=arg)
		
		await ctx.send(embed=eObj)

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

		print("[HealthChecks help()] numberOfCommands set to "+str(numberOfCommands))
		helpArr = [["" for x in range(2)] for y in range(numberOfCommands)] 
		index=0
		logger.info("[HealthChecks help()] tranferring dictionary to array")
		for entry in helpDict['commands']:
			if entry['access'] == "bot_manager" and ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
				print("[HealthChecks help()] adding "+str(entry)+" to index "+str(index)+" of the helpArr")
				helpArr[index][0]=entry['name']
				helpArr[index][1]=entry['description']
				index+=1
			elif entry['access'] == "public":
				print("[HealthChecks help()] adding "+str(entry)+" to index "+str(index)+" of the helpArr")
				helpArr[index][0]=entry['name']
				helpArr[index][1]=entry['description']
				index+=1
			
		logger.info("[HealthChecks help()] transfer successful")

		await paginateEmbed(bot=self.bot,title="Help Page" ,ctx=ctx,listToEmbed=helpArr, numOfPageEntries=5, add_field=True)
		#rolesList = sorted(rolesList, key=str.lower)


def setup(bot):
	bot.add_cog(HealthChecks(bot))
