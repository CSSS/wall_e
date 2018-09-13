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
			logger.error("[Reminders remindme()] was unable to extract a time")
			await ctx.send("RemindMeIn Error:\n```unable to extract a time"+str(how_to_call_command)+"```")
			return
		if message == '':
			logger.error("[Reminders remindme()] was unable to extract a message")
			await ctx.send("RemindMeIn Error:\n```unable to extract a message"+str(how_to_call_command)+"```")
			return
		timeUntil = str(parsedTime)
		logger.info("[Reminders remindme()] extracted time is "+str(timeUntil))
		logger.info("[Reminders remindme()] extracted message is "+str(message))
		time_struct, parse_status = parsedatetime.Calendar().parse(timeUntil)
		if parse_status == 0:
			logger.error("[Reminders remindme()] couldn't parse the time")
			await ctx.send('RemindMeIn Error:\n```Could not parse time!'+how_to_call_command+'```')
			return
		expire_seconds = int(mktime(time_struct) - time.time())
		json_string = json.dumps({'cid': ctx.channel.id, 'mid': ctx.message.id})
		r = self.r
		r.set(json_string, '', expire_seconds)
		fmt = '```Reminder set for {0} seconds from now```'
		await ctx.send(fmt.format(expire_seconds))
		logger.info("[Reminders remindme()] reminder has been contructed and sent.")

	@commands.command()
	async def showreminders(self, ctx):
		logger.info("[Reminders showreminders()] remindme command detected from user "+str(ctx.message.author))
		if self.r is not None:
			try:
				reminders=''
				logger.info("[Reminders showreminders()] iterating through all the keys in the database")
				for key in self.r.scan_iter("*"):
					keyValue = json.loads(key)
					logger.info("[Reminders showreminders()] acquired key "+str(keyValue))
					chan = self.bot.get_channel(keyValue['cid'])
					if chan is not None:
						logger.info("[Reminders showreminders()] acquired valid channel "+str(chan))
						msg = await chan.get_message(keyValue['mid'])
						logger.info("[Reminders showreminders()] acquired the messsage "+str(msg))
						reminderCtx = await self.bot.get_context(msg)
						if reminderCtx.valid and helper_files.testenv.TestCog.check_test_environment(reminderCtx):
							if reminderCtx.message.author  == ctx.message.author:
								logger.info("[Reminders showreminders()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
								reminders+=str(keyValue['mid'])+"   "+reminderCtx.message.content+"\n"
				author = ctx.author.nick or ctx.author.name
				if reminders != '':
					logger.info("[Reminders showreminders()] sent off the list of reminders to "+str(ctx.message.author))
					await ctx.send("Here are your reminders "+ author+"\n```"+"MessageID\t\t\tReminder\n"+reminders+"```")
				else:
					logger.info("[Reminders showreminders()] "+str(ctx.message.author)+" didnt seem to have any reminders.")
					await ctx.send("You dont seem to have any reminders "+ author)
			except Exception as error:
				await ctx.send("Something screwy seems to have happened, look at the logs for more info.")
				logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

	@commands.command()
	async def deletereminder(self,ctx,messageId):
		logger.info("[Reminders deletereminder()] deletereminder command detected from user "+str(ctx.message.author))
		if self.r is not None:
			reminderExists=False
			try:
				reminder=''
				logger.info("[Reminders deletereminder()] iterating through all the keys in the database")
				for key in self.r.scan_iter("*"):
					keyValue = json.loads(key)
					logger.info("[Reminders deletereminder()] acquired key "+str(keyValue))
					if keyValue['mid'] == int(messageId):
						reminderExists = True
						logger.info("[Reminders deletereminder()] determined that it was the key the user wants to delete")
						chan = self.bot.get_channel(keyValue['cid'])
						if chan is not None:
							logger.info("[Reminders deletereminder()] acquired valid channel "+str(chan))
							msg = await chan.get_message(keyValue['mid'])
							logger.info("[Reminders deletereminder()] acquired the messsage "+str(msg))
							reminderCtx = await self.bot.get_context(msg)
							if reminderCtx.valid and helper_files.testenv.TestCog.check_test_environment(reminderCtx):
								if reminderCtx.message.author  == ctx.message.author:
									logger.info("[Reminders deletereminder()] determined that message did originate with "+str(ctx.message.author)+", adding to list of reminders")
									reminder=reminderCtx.message.content
									logger.info("[Reminders deletereminder()] following reminder was deleted = "+reminderCtx.message.content)
									await ctx.send("deleteReminder\n```Following reminder has been deleted:\n"+reminder+"```")
									self.r.delete(key)
								else:
									await ctx.send("deleteReminder ERROR\n```You are trying to delete a reminder that is not yours```")
									logger.info("[Reminders deletereminder()] It seems that  "+str(ctx.message.author)+" was trying to delete "+str(reminderCtx.message.author)+"'s reminder.")
				if not reminderExists:
					await ctx.send("deleteReminder ERROR\n```Specified reminder could not be found```")
					logger.info("[Reminders deletereminder()] Specified reminder could not be found ")
			except Exception as error:
				logger.error('[Reminders.py showreminders()] Ignoring exception when generating reminder:')
				traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

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
							logger.info('[Reminders.py get_message()] sent off reminder to '+str(ctx.message.author)+" about \""+ctx.message.content+"\"")
							await ctx.send(fmt.format(ctx.message.author.id, ctx.message.content))
				except Exception as error:
					logger.error('[Reminders.py get_message()] Ignoring exception when generating reminder:')
					traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
			await asyncio.sleep(2)

def setup(bot):
	bot.add_cog(Reminders(bot))