from discord.ext import commands
import logging
import requests as req
from helper_files.embed import embed 
import helper_files.settings as settings
import json
from main import wolframAPI, wolframClient

logger = logging.getLogger('wall_e')


class Misc():

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def poll(self, ctx, *questions):
		logger.info("[Misc poll()] poll command detected from user "+str(ctx.message.author))
		name = ctx.author.display_name
		ava = ctx.author.avatar_url

		if len(questions) > 12:
			logger.info("[Misc poll()] was called with too many options.")
			eObj = embed(title='Poll Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='Please only submit a maximum of 11 options for a multi-option question.')
			await ctx.send(embed=eObj)
			return
		elif len(questions) == 1:
			logger.info("[Misc poll()] yes/no poll being constructed.")
			eObj = embed(title='Poll', author=name, avatar=ava, description=questions[0])
			post = await ctx.send(embed=eObj)
			await post.add_reaction(u"\U0001F44D")
			await post.add_reaction(u"\U0001F44E")
			logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
			return
		if len(questions) == 2:
			logger.info("[Misc poll()] poll with only 2 arguments detected.")
			eObj = embed(title='Poll Error', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='Please submit at least 2 options for a multi-option question.')
			await ctx.send(embed=eObj)
			return
		elif len(questions) == 0:
			logger.info("[Misc poll()] poll with no arguments detected.")
			eObj = embed(title='Usage', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description='.poll <Question> [Option A] [Option B] ...')
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
			eObj = embed(title='Poll:', author=name, avatar=ava, description=question, content=content)
			pollPost = await ctx.send(embed=eObj)

			logger.info("[Misc poll()] multi-option poll message contructed and sent.")
			for i in range(0, options):
				await pollPost.add_reaction(numbersUnicode[i])
			logger.info("[Misc poll()] reactions added to multi-option poll message.")

	@commands.command()
	async def urban(self, ctx, *arg):
		logger.info("[Misc urban()] urban command detected from user "+str(ctx.message.author)+" with argument =\""+str(arg)+"\"")
		logger.info("[Misc urban()] query string being contructed")
		queryString = ''
		for x in arg:
			queryString += x + '%20'
		queryString = queryString[:len(queryString)-3]
		
		url = 'http://api.urbandictionary.com/v0/define?term=%s' % queryString
		logger.info("[Misc urban()] following url  constructed for get request =\""+str(url)+"\"")
		

		res = req.get(url)
		logger.info("[Misc urban()] Get request made =\""+str(res)+"\"")
		
		if(res.status_code != 404):
			logger.info("[Misc urban()] Get request successful")			
			data = res.json()
			data = data['list']
		else:
			logger.info("[Misc urban()] Get request failed, 404 resulted")
			data = ''

		if not data:
			logger.info("[Misc urban()] sending message indicating 404 result")
			eObj = embed(title="Urban Results", author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xfd6a02, description=":thonk:404:thonk:You searched something dumb didn't you?")
			await ctx.send(embed=eObj)
			return
		else:
			logger.info("[Misc urban()] constructing embed object with definition of \"" + queryString+"\"")
			content = [
				['Definition', data[0]['definition'][:200] + '\n(...)'], 
				['Link', '[here](%s)' % data[0]['permalink']]
				]
			eObj = embed(title='Results from Urban Dictionary', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xfd6a02, content=content)
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
			eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xdd1100, content=content)
			await ctx.send(embed=eObj)
			logger.info("[Misc wolfram()] result found for %s" % arg)
		except (AttributeError, StopIteration):
			content = [
				['Results from Wolfram Alpha', "No results found. :thinking: \n\n[Link](%s)" % wolframURL], 
				]
			eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, colour=0xdd1100, content=content)
			await ctx.send(embed=eObj)
			logger.error("[Misc wolfram()] result NOT found for %s" % arg)


def setup(bot):
	bot.add_cog(Misc(bot))
