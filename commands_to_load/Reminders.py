from discord.ext import commands
import json
import logging
import redis
import asyncio
import parsedatetime
import time
from time import mktime
import helper_files.testenv
import traceback
import sys
import helper_files.settings as settings
from helper_files.embed import embed

logger = logging.getLogger('wall_e')

class Reminders():

	def __init__(self, bot):
		self.bot = bot

		#setting up database connection
		try:
			self.r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
			self.message_subscriber = self.r.pubsub(ignore_subscribe_messages=True)
			self.message_subscriber.subscribe('__keyevent@0__:expired')
			self.bot.loop.create_task(self.get_messages())
			logger.info("[Reminders __init__] redis connection established")
		except Exception as e:
			logger.error("[Reminders __init__] enountered following exception when setting up redis connection\n{}".format(e))

	@commands.command()
	async def remindmein(self, ctx, *args):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		fmt = 'This command is offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		fmt = 'This command is offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

	@commands.command()
	async def deletereminder(self,ctx):
		logger.info("[Reminders remindme()] remindme command detected from user "+str(ctx.message.author))
		fmt = 'This command is offline, sorry.'
		eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt)
		await ctx.send(embed=eObj)
		logger.info("[Reminders remindme()] offline message has been sent.")

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
							fmt = '<@{0}>\n {1}'
							logger.info('[Misc.py get_message()] sent off reminder to '+str(ctx.message.author)+" about \""+ctx.message.content+"\"")
							eObj = embed(author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=fmt.format(ctx.message.author.id, ctx.message.content), footer='Reminder')
							await ctx.send(embed=eObj)
				except Exception as error:
					logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Reminders(bot))
