from discord.ext import commands
import discord.client
import json
from helper_files.Paginate import paginateEmbed
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
			if entry['access'] == "Bot_manager" and ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
				if 'Class' not in entry['name']:
					numberOfCommands += 1
			elif entry['access'] == "Minions" and (ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members or ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members):
				if 'Class' not in entry['name']:
					numberOfCommands += 1					
			elif entry['access'] == "public":
				if 'Class' not in entry['name']:
					numberOfCommands += 1

		print("[HealthChecks help()] numberOfCommands set to "+str(numberOfCommands))


		numOfPages, numOfPageEntries = determineNumOfPagesAndEntries(numberOfEntriesToPaginate=numberOfCommands, numOfPageEntries=5)
		descriptionToEmbed = ["" for y in range(numOfPages)] 
		logger.info("[HealthChecks help()] tranferring dictionary to array")
		x, page = 0, 0;
		for entry in helpDict['commands']:
			if entry['access'] == "Bot_manager" and ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members:
				if 'Class' in entry['name']:
					print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
					descriptionToEmbed[page]+="\n**"+entry['name']+"**: "+"\n"
				else:
					print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")					
					descriptionToEmbed[page]+="*"+entry['name']+"* - "+entry['description']+"\n\n"
					x+=1
					if x == numOfPageEntries:
						page+=1
						x = 0					
			elif entry['access'] == "Minions" and (ctx.message.author in discord.utils.get(ctx.guild.roles, name="Bot_manager").members or ctx.message.author in discord.utils.get(ctx.guild.roles, name="Minions").members):
				if 'Class' in entry['name']:
					print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
					descriptionToEmbed[page]+="\n**"+entry['name']+"**: "+"\n"					
				else:
					print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
					descriptionToEmbed[page]+="*"+entry['name']+"* - "+entry['description']+"\n\n"
					x+=1
					if x == numOfPageEntries:
						page+=1
						x = 0
			elif entry['access'] == "public":
				print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
				if 'Class' in entry['name']:
					print("[HealthChecks help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
					descriptionToEmbed[page]+="\n**"+entry['name']+"**: "+"\n"
				else:
					descriptionToEmbed[page]+="*"+entry['name']+"* - "+entry['description']+"\n\n"
					x+=1
					if x == numOfPageEntries:
						page+=1
						x = 0
			else:
				print("[HealthChecks help()] "+str(entry)+" has a wierd access level of "+str(entry['access'])+"....not sure how to handle it so not adding it to the descriptionToEmbed")
		logger.info("[HealthChecks help()] transfer successful")

		await paginateEmbed(self.bot, ctx, descriptionToEmbed, numOfPages, numOfPageEntries, title="Help Page" )


def setup(bot):
	bot.add_cog(HealthChecks(bot))
