import time
import parsedatetime
import json
from discord.ext import commands
from time import mktime
import logging
import redis
import asyncio
import traceback
import sys
import helper_files.testenv

logger = logging.getLogger('wall_e')


class Misc():

	def __init__(self, bot):
		self.bot = bot

		#setting up database connection
		try:
			self.r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
			self.message_subscriber = self.r.pubsub(ignore_subscribe_messages=True)
			self.message_subscriber.subscribe('__keyevent@0__:expired')
			self.bot.loop.create_task(self.get_messages())
			logger.info("[Misc __init__] redis connection established")
		except Exception as e:
			logger.error("[Misc __init__] enountered following exception when setting up redis connection\n{}".format(e))




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


	@commands.command()
	async def remindmein(self, ctx, *args):
		logger.info("[Misc remindme()] remindme command detected from user "+str(ctx.message.author))
		parsedTime=''
		message=''
		parseTime=True
		for index, value in enumerate(args):
			if parseTime == True:
				if value == 'to':
					parseTime = False
				else:
					parsedTime+=str(value)+" "
			else:
				message+=str(value)+" "
		how_to_call_command="\nPlease call command like so:\nremindmein <time|minutes|hours|days> to <what to remind you about>\nExample: \".remindmein 10 minutes to turn in my assignment\""
		if parsedTime == '':
			logger.error("[Misc remindme()] was unable to extract a time")
			await ctx.send("RemindMeIn Error:\n```unable to extract a time"+str(how_to_call_command)+"```")
			return
		if message == '':
			logger.error("[Misc remindme()] was unable to extract a message")
			await ctx.send("RemindMeIn Error:\n```unable to extract a message"+str(how_to_call_command)+"```")
			return
		timeUntil = str(parsedTime)
		logger.info("[Misc remindme()] extracted time is "+str(timeUntil))
		logger.info("[Misc remindme()] extracted message is "+str(message))
		time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
		if parse_status == 0:
			logger.error("[Misc remindme()] couldn't parse the time")
			await ctx.send('RemindMeIn Error:\n```Could not parse time!'+how_to_call_command+'```')
			return
		expire_seconds = int(mktime(time_struct) - time.time())
		json_string = json.dumps({'cid': ctx.channel.id, 'mid': ctx.message.id})
		r = self.r
		r.set(json_string, '', expire_seconds)
		fmt = '```Reminder set for {0} seconds from now```'
		await ctx.send(fmt.format(expire_seconds))
		logger.info("[Misc remindme()] reminder has been contructed and sent.")

#########################################
## Background function that determines ##
## if a reminder's time has come       ##
## to be sent to its channel           ##
#########################################
	async def get_messages(self):
		await self.bot.wait_until_ready()
		while True:
			message = self.message_subscriber.get_message()
			if message is not None and message['type'] == 'message':
				try:
					cid_mid_dct = json.loads(message['data'])
					chan = self.bot.get_channel(cid_mid_dct['cid'])
					if chan is not None:
						msg = await chan.get_message(cid_mid_dct['mid'])
						ctx = await self.bot.get_context(msg)
						if ctx.valid and helper_files.testenv.TestCog.check_test_environment(ctx):
							fmt = '<@{0}> ```{1}```'
							logger.info('[Misc.py get_message()] sent off reminder to '+str(ctx.message.author)+" about \""+ctx.message.content+"\"")
							await ctx.send(fmt.format(ctx.message.author.id, ctx.message.content))
				except Exception as error:
					logger.error('[Misc.py get_message()] Ignoring exception when generating reminder:')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Misc(bot))
