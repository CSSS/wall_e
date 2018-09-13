from discord.ext import commands
import logging

logger = logging.getLogger('wall_e')


class Misc():

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def poll(self, ctx, *questions):
		logger.info("[Misc poll()] poll command detected from user "+str(ctx.message.author))
		if len(questions) > 12:
			logger.error("[Misc poll()] was called with too many options.")
			await ctx.send("Poll Error:\n```Please only submit a maximum of 11 options for a multi-option question.```")
			return
		elif len(questions) == 1:
			logger.info("[Misc poll()] yes/no poll being constructed.")
			post = await ctx.send("Poll:\n" + "```" + questions[0] + "```")
			await post.add_reaction(u"\U0001F44D")
			await post.add_reaction(u"\U0001F44E")
			logger.info("[Misc poll()] yes/no poll constructed and sent to server.")
			return
		if len(questions) == 2:
			logger.error("[Misc poll()] poll with only 2 arguments detected.")
			await ctx.send("Poll Error:\n```Please submit at least 2 options for a multi-option question.```")
			return
		elif len(questions) == 0:
			logger.error("[Misc poll()] poll with no arguments detected.")
			await ctx.send('```Usage: .poll <Question> [Option A] [Option B] ...```')
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
			pollPost = await ctx.send("Poll:\n```" + question + "```" + optionString)
			logger.info("[Misc poll()] multi-option poll message contructed and sent.")
			for i in range(0, options):
				await pollPost.add_reaction(numbersUnicode[i])
			logger.info("[Misc poll()] reactions added to multi-option poll message.")


def setup(bot):
	bot.add_cog(Misc(bot))
