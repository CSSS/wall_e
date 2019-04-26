from discord.ext import commands
import logging
import aiohttp
from helper_files.embed import embed 
from helper_files.Paginate import paginateEmbed
from helper_files.listOfRoles import getListOfUserPerms
import helper_files.settings as settings
import json
import wolframalpha
import discord.client
import urllib
import asyncio

logger = logging.getLogger('wall_e')
client = discord.Client()

wolframClient = wolframalpha.Client(settings.wolframAPI)

class Misc():

	def __init__(self, bot):
		self.bot = bot
		self.session = aiohttp.ClientSession(loop=bot.loop)

	@commands.command()
	async def poll(self, ctx, *questions):
		logger.info("[Misc poll()] poll command detected from user "+str(ctx.message.author))
		name = ctx.author.display_name
		ava = ctx.author.avatar_url

		if len(questions) > 12:
			logger.info("[Misc poll()] was called with too many options.")
			eObj = await embed(ctx, title='Poll Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='Please only submit a maximum of 11 options for a multi-option question.')
			if eObj is not False:
				await ctx.send(embed=eObj)
			return
		elif len(questions) == 1:
			logger.info("[Misc poll()] yes/no poll being constructed.")
			eObj = await embed(ctx, title='Poll', author=name, avatar=ava, description=questions[0])
			if eObj is not False:
				post = await ctx.send(embed=eObj)
				await post.add_reaction(u"\U0001F44D")
				await post.add_reaction(u"\U0001F44E")
				logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
			return
		if len(questions) == 2:
			logger.info("[Misc poll()] poll with only 2 arguments detected.")
			eObj = await embed(ctx, title='Poll Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='Please submit at least 2 options for a multi-option question.')
			if eObj is not False:
				await ctx.send(embed=eObj)
			return
		elif len(questions) == 0:
			logger.info("[Misc poll()] poll with no arguments detected.")
			eObj = await embed(ctx, title='Usage', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='.poll <Question> [Option A] [Option B] ...')
			if eObj is not False:
				await ctx.send(embed=eObj)
			return
		else:
			logger.info("[Misc poll()] multi-option poll being constructed.")
			questions = list(questions)
			optionString = "\n"
			numbersEmoji = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]
			numbersUnicode = [u"0\u20e3", u"1\u20e3", u"2\u20e3", u"3\u20e3", u"4\u20e3", u"5\u20e3", u"6\u20e3", u"7\u20e3", u"8\u20e3", u"9\u20e3", u"\U0001F51F"]
			question = questions.pop(0)
			options = 0
			for m, n in zip(numbersEmoji, questions):
				optionString += m + ": " + n +"\n"
				options += 1
			
			content = [['Options:', optionString]]
			eObj = await embed(ctx, title='Poll:', author=name, avatar=ava, description=question, content=content)
			if eObj is not False:
				pollPost = await ctx.send(embed=eObj)
				logger.info("[Misc poll()] multi-option poll message contructed and sent.")

				for i in range(0, options):
					await pollPost.add_reaction(numbersUnicode[i])
				logger.info("[Misc poll()] reactions added to multi-option poll message.")

	@commands.command()
	async def urban(self, ctx, *arg):
		logger.info("[Misc urban()] urban command detected from user "+str(ctx.message.author)+" with argument =\""+str(arg)+"\"")

		queryString = urllib.parse.urlencode({ 'term' : " ".join(arg)})
		url = 'http://api.urbandictionary.com/v0/define?%s' % queryString

		logger.info("[Misc urban()] following url  constructed for get request =\""+str(url)+"\"")

		async with self.session.get(url) as res:
			data = ''
			if res.status == 200:
				logger.info("[Misc urban()] Get request successful")
				data = await res.json()
			else:
				logger.info("[Misc urban()] Get request failed resulted in " + str(res.status))

			data = data['list']
			if not data:
				logger.info("[Misc urban()] sending message indicating 404 result")
				eObj = await embed(ctx, title="Urban Results", author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xfd6a02, description=":thonk:404:thonk:You searched something dumb didn't you?")
				if eObj is not False:
					await ctx.send(embed=eObj)
				return
			else:
				logger.info("[Misc urban()] constructing embed object with definition of \"" + " ".join(arg)+"\"")
				urbanUrl = 'https://www.urbandictionary.com/define.php?%s' % queryString
				# truncate to fit in embed, field values must be 1024 or fewer in length
				definition = data[0]['definition'][:1021] + '...' if len(data[0]['definition']) > 1024 else data[0]['definition']
				content = [
					['Definition', definition],
					['Link', '[here](%s)' % urbanUrl]
					]
				eObj = await embed(ctx, title='Results from Urban Dictionary', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xfd6a02, content=content)
				if eObj is not False:
					await ctx.send(embed=eObj)

	@commands.command()
	async def wolfram(self, ctx, *arg):
		arg = " ".join(arg)
		logger.info("[Misc wolfram()] wolfram command detected from user "+str(ctx.message.author)+" with argument =\""+str(arg)+"\"")
		logger.info("[Misc wolfram()] URL being contructed")

		commandURL = arg.replace("+", "%2B")
		commandURL = commandURL.replace("(", "%28")
		commandURL = commandURL.replace(")", "%29")
		commandURL = commandURL.replace("[", "%5B")
		commandURL = commandURL.replace("]", "%5D")
		commandURL = commandURL.replace(" ", "+")
		wolframURL = 'https://www.wolframalpha.com/input/?i=%s' % commandURL

		logger.info("[Misc wolfram()] querying WolframAlpha for %s" % arg)
		res = wolframClient.query(arg)
		try:
			content = [
				['Results from Wolfram Alpha', "`" + next(res.results).text + "`" + "\n\n[Link](%s)" % wolframURL]
				]
			eObj = await embed(ctx, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xdd1100, content=content)
			if eObj is not False:
				await ctx.send(embed=eObj)
				logger.info("[Misc wolfram()] result found for %s" % arg)
		except (AttributeError, StopIteration):
			content = [
				['Results from Wolfram Alpha', "No results found. :thinking: \n\n[Link](%s)" % wolframURL], 
				]
			eObj = await embed(ctx, author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xdd1100, content=content)
			if eObj is not False:
				await ctx.send(embed=eObj)
				logger.error("[Misc wolfram()] result NOT found for %s" % arg)

	async def GeneralDescription(self, ctx):
		numberOfCommandsPerPage=5
		logger.info("[Misc help()] help command detected from "+str(ctx.message.author))
		logger.info("[Misc help()] attempting to load command info from help.json")
		with open('commands_to_load/help.json') as f:
			helpDict = json.load(f)
		logger.info("[Misc help()] loaded commands from help.json=\n"+str(json.dumps(helpDict, indent=3)))
		user_perms = await getListOfUserPerms(ctx)
		user_roles = [role.name for role in sorted(ctx.author.roles, key = lambda x: int(x.position),reverse=True)]
		descriptionToEmbed=[""]
		x, page = 0, 0
		for entry in helpDict['commands']:
			if entry['access'] == "role":
				for role in entry[entry['access']]:
					if ( role in user_roles or (role == 'public') ):
						if 'Class' in entry['name'] and 'Bot_manager' in user_roles:
							logger.info("[Misc help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
							descriptionToEmbed[page]+="\n**"+entry['name']+"**: "+"\n"
						else:
							logger.info("[Misc help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")
							descriptionToEmbed[page]+="*"+"/".join(entry['name'])+"* - "+entry['description'][0]+"\n\n"
							x+=1
							if x == numberOfCommandsPerPage:
								descriptionToEmbed.append("")
								page+=1
								x  = 0
			elif entry['access'] == "permissions":
				for permission in entry[entry['access']]:
					if permission in user_perms:
						logger.info("[Misc help()] adding "+str(entry)+" to page "+str(page)+" of the descriptionToEmbed")					
						descriptionToEmbed[page]+="*"+"/".join(entry['name'])+"* - "+entry['description'][0]+"\n\n"
						x+=1
						if x == numberOfCommandsPerPage:
							descriptionToEmbed.append("")
							page+=1
							x = 0	
						break			
			else:
				logger.info("[Misc help()] "+str(entry)+" has a wierd access level of "+str(entry['access'])+"....not sure how to handle it so not adding it to the descriptionToEmbed")
		logger.info("[Misc help()] transfer successful")

		await paginateEmbed(self.bot, ctx, descriptionToEmbed, title="Help Page" )

	async def specificDescription(self, ctx, command):
		with open('commands_to_load/help.json') as f:
			helpDict = json.load(f)
		helpDict = helpDict['commands']
		logger.info("[Misc specificDescription()] invoked by user "+str(ctx.message.author)+" for command "+str(command))
		for entry in helpDict:
			for name in entry['name']:
				if name == command[0]:
					logger.info("[Misc specificDescription()] loading the entry for command  "+str(command[0])+" :\n\n"+str(entry))
					descriptions = ""
					for description in entry['description']:
						descriptions+= description+"\n\n"
					descriptions+="\n\nExample:\n"
					descriptions+="\n".join(entry['example'])
					eObj = await embed(ctx,title="Man Entry for "+str(command[0]), author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=descriptions)
					if eObj is not False:
						msg = await ctx.send(content=None, embed=eObj)
						logger.info("[Misc specificDescription()] embed created and sent for command "+str(command[0]))
						await msg.add_reaction('✅')
						logger.info("[Misc specificDescription()] reaction added to message")
						def checkReaction(reaction, user):
							if not user.bot:  ##just making sure the bot doesnt take its own reactions
								##into consideration
								e = str(reaction.emoji)
								logger.info("[Misc specificDescription()] reaction " + e + " detected from " + str(user))
								return e.startswith(('✅'))
						userReacted = False
						while userReacted == False:
							try:
								userReacted = await self.bot.wait_for('reaction_add', timeout=20, check=checkReaction)
							except asyncio.TimeoutError:
								logger.info("[Misc specificDescription()] timed out waiting for the user's reaction.")

							if userReacted != False:
								if '✅' == userReacted[0].emoji:
									logger.info("[Misc specificDescription()] user indicates they are done with the roles command, deleting roles message")
									await msg.delete()
									return
							else:
								logger.info("[Misc specificDescription()] deleting message")
								await msg.delete()
								return		

	@commands.command(aliases=['man'])
	async def help(self, ctx, *arg):
		await ctx.send("     help me.....")
		logger.info("[Misc help()] help command detected from "+str(ctx.message.author)+" with the argument "+str(arg))
		if len(arg) == 0:
			await self.GeneralDescription(ctx)
		else:
			await self.specificDescription(ctx, arg)

	@client.event
	async def on_message_delete(message):
		if(message.author.id == "556251463538442253"): # imlate#6365
			bot_commands_channel = client.get_channel(354084037465473025)
			await bot_commands_channel.send('imlate deleted: ' + message)
			#await message.channel.send('imlate deleted: ' + message)
            
            
	def __del__(self):
		self.session.close()
		client.logout()

def setup(bot):
	bot.add_cog(Misc(bot))
